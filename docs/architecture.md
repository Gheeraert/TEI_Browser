# Architecture

Ce document décrit les couches du lecteur TEI, les décisions prises et
leurs justifications, pour permettre à tout développeur de reprendre le
projet. Le contrat de rendu HTML est décrit dans [contrat-html.md](contrat-html.md).

## Vue d'ensemble

```
              ┌─────────────────────────────────────────────┐
 interfaces   │  cli.py          ui/pyside_app.py           │
 (couches     │  (render/view/    (desktop PySide6)         │
  minces)     │   inspect/profiles/gui/webview)             │
              └───────────────────┬─────────────────────────┘
                                  │  appelle uniquement
              ┌───────────────────▼─────────────────────────┐
 façade       │  core/service.py : render(), inspect_file()  │
              │  profiles/loader.py : profils JSON           │
              └───┬──────────────┬──────────────┬───────────┘
                  │              │              │
        ┌─────────▼───┐  ┌───────▼──────┐  ┌────▼──────────┐
        │ core/        │  │ profiles/    │  │ transform/    │
        │ document.py  │  │ loader.py    │  │ engine.py     │
        │ (lxml sûr,   │  │ (JSON ->     │  │ (interface)   │
        │ inventaire)  │  │  Profile)    │  │ saxon_engine  │
        └──────────────┘  └──────────────┘  └───────────────┘
                                  │
                          resources/ : xsl/, css/, profiles/
```

## Flux d'un rendu

1. **Chargement du profil** (`profiles/loader.py`) : JSON → feuille XSLT,
   paramètres, CSS. Profil inconnu → `RenderResult` d'erreur, pas d'exception.
2. **Parsing sécurisé** (`core/document.py`) : lxml avec entités externes,
   DTD et réseau désactivés. XML mal formé → erreur propre `xml-error`.
3. **Inventaire** : les éléments du document sont comparés à
   `HANDLED_ELEMENTS` (liste synchronisée avec `tei-common.xsl`) et
   produisent les diagnostics `unknown-elements`, `non-tei-elements`,
   `minimal-rendering`, `signaled-only`.
4. **Transformation** (`transform/saxon_engine.py`) : SaxonC-HE compile la
   XSLT, reçoit les paramètres du profil (plus `css-hrefs`), retourne le HTML.
5. **Écriture** : HTML dans le dossier de sortie, CSS du profil copiées à
   côté, diagnostics sérialisés en JSON (`<nom>.diagnostics.json`).

Le service **ne lève jamais d'exception pour un problème de données** :
tout est retourné dans `RenderResult` (`ok`, `html_path`, `diagnostics`).
Seuls les bugs de programmation remontent.

## Décisions et justifications

### SaxonC en appel direct (pas de sous-processus)

`saxonche` (SaxonC-HE, MPL-2.0) est appelé directement dans le processus.
Le `PySaxonProcessor` est un **singleton de module** jamais fermé : créer et
détruire plusieurs processeurs dans un même processus a causé des
instabilités dans certaines versions de SaxonC.

L'isolation en sous-processus (prévue dans l'architecture initiale contre
les crashs natifs) a été différée : si elle devient nécessaire (segfaults
constatés, packaging), elle s'implémente comme une nouvelle classe
respectant `TransformEngine`, sans toucher au reste.

**Règle : seul `transform/saxon_engine.py` importe saxonche.** C'est le
verrou anti-dépendance : remplacer le moteur = remplacer un module.

### Diagnostics par analyse lxml, pas par xsl:message

Les diagnostics sont produits en Python (`core/document.py :: analyze`)
plutôt que par des `xsl:message` interceptés : la récupération des
messages de SaxonC côté Python est fragile, et l'analyse lxml fonctionne
même si la transformation échoue. L'analyse produit :

- l'inventaire des éléments (non traités / hors TEI / rendu minimal /
  hors rendu) par comparaison à `HANDLED_ELEMENTS` ;
- un **résumé chiffré** (éléments distincts, occurrences non traitées,
  comptes de `note`, `app`, `pb`, `graphic`) inclus dans le JSON ;
- la vérification des **références locales** `#id` (`ref`, `target`,
  `corresp`, `ana`, `wit`, `who`, `facs`) → `broken-local-ref` ;
- la vérification des **médias locaux** (`graphic/@url`, `pb/@facs`)
  → `missing-media`.

Codes de diagnostic : `xml-error` (bloquant), `transform-error`
(bloquant), `profile-unknown` / `profile-invalid` / `missing-xslt` /
`missing-css` (bloquants), `not-tei`, `unknown-elements`,
`non-tei-elements`, `broken-local-ref`, `missing-media` (warnings),
`minimal-rendering`, `signaled-only` (infos).

La synchronisation `HANDLED_ELEMENTS` ↔ templates de `tei-common.xsl`
est **vérifiée automatiquement** par `tests/test_contract_sync.py`, qui
extrait les noms `tei:*` des attributs `@match` de la XSLT et les compare
aux ensembles Python. Toute divergence fait échouer la suite de tests.

### Profils hybrides

Un profil JSON = XSLT d'entrée + paramètres + CSS. Trois niveaux de
personnalisation, du plus courant au plus rare :

1. **CSS** : tout le visuel (italiques, thèmes, visibilité des variantes) ;
2. **paramètres XSLT** : booléens et scalaires (`show-pb`...) ;
3. **surcharge XSLT** : seulement quand la *structure* HTML change
   (futurs `drama.xsl`, `verse.xsl`... qui importeront `tei-common.xsl`).

Les niveaux 1 et 2 ne demandent jamais de toucher au XSLT, et sont
directement portables vers un futur lecteur navigateur.

### Médias locaux : l'existence est vérifiée par Python, pas par la XSLT

Une XSLT ne sait pas tester l'existence d'un fichier. Pour afficher les
images locales, `core/document.py` vérifie sur disque les chemins de
`graphic/@url` et `pb/@facs`. Seuls les chemins relatifs locaux, sans
schéma, relatifs au dossier du fichier TEI source, sont résolus. Les URL,
les chemins absolus POSIX ou Windows, les chemins UNC, les URL
protocol-relative et les remontées par `..` sont rejetés. `core/service.py`
transmet ensuite à la XSLT deux paramètres calculés :
`existing-media` (les valeurs trouvées, séparées par des sauts de ligne)
et `media-base` (le dossier source en URI `file:`, car le HTML est écrit
ailleurs). La XSLT rend alors une vraie `<img>` (ou un lien pour `pb`),
sinon le marqueur textuel. Les références `#id` et les ressources distantes
sont ignorées pour les médias : **aucune ressource distante n'est jamais
chargée**.

### Snapshots HTML normalisés

`tests/test_snapshots.py` compare le HTML produit pour chaque couple
(échantillon, profil) à un snapshot stocké dans `tests/snapshots/`.
La normalisation (`tests/snapshot_common.py`) est volontairement légère :
elle neutralise seulement les chemins `file:` absolus et les identifiants
générés des notes, puis compare ligne à ligne. Régénération **volontaire**
uniquement :

```powershell
.\.venv\Scripts\python tests\update_snapshots.py
```

puis relecture du diff git des snapshots avant commit.

### Suggestion de profil : heuristique par règles, pas de ML

`inspect` propose un profil par des règles simples et documentées
(`core/document.py :: _suggest_profile`), dans cet ordre :
`sp`/`speaker` → drama ; `lg` ou ≥ 10 `l` → verse ; `opener`/`closer` →
correspondence ; sinon prose. Le théâtre passe en premier car une pièce
en vers contient aussi des `lg`/`l`. La suggestion est indicative
(`suggested_profile` + `suggestion_reason` dans le résumé), jamais
appliquée automatiquement.

### Sécurité

- lxml : `resolve_entities=False`, `no_network=True`, `load_dtd=False` —
  le fichier est validé avant tout passage à Saxon.
- HTML produit : CSP `default-src 'none'` (aucun script), styles et images
  limités à `'self'` et au schéma `file:` (`'self'` est inopérant sous
  `file://`, origine opaque).
- Aucun JavaScript n'est généré ni injecté dans le rendu.
- Sorties dans un dossier explicite choisi par l'utilisateur (`--out`),
  pas de fichiers temporaires anonymes : rendu reproductible et inspectable.

## Interface desktop expérimentale

L'interface principale lancée par `tei-reader gui` ou
`python -m tei_reader gui` est une application PySide6 (`ui/pyside_app.py`).
L'ancienne interface pywebview reste disponible par `tei-reader webview` et
le visualiseur simple `tei-reader view` continue d'ouvrir un HTML rendu dans
une webview.

La couche PySide reste mince : elle appelle `render()`, `inspect_file()`,
`list_profiles()` et `load_profile()`, puis affiche le HTML produit, les
diagnostics et le résumé d'inspection. Elle ne parse pas elle-même le XML, ne
touche pas directement à Saxon, ne connaît pas les détails de la XSLT et ne
duplique pas les diagnostics. Cette frontière est volontaire : les prochains
enrichissements TEI doivent faire évoluer la couche métier et le contrat
HTML, tandis que l'interface reste un lecteur de résultats.

`QWebEngineView` est utilisé pour l'aperçu HTML quand QtWebEngine est
disponible. Sinon, l'interface doit échouer clairement ou proposer l'ouverture
du HTML dans le navigateur externe, sans tenter de réinterpréter le contrat
HTML dans un composant simplifié.

## Horizon navigateur (rappel des décisions)

Le capital portable vers une future extension Firefox est, par ordre
d'importance :

1. le **contrat HTML** ([contrat-html.md](contrat-html.md)) — classes
   `tei-*`, `data-tei-*`, fallback `data-tei` ;
2. les **profils JSON** ;
3. les **CSS** ;
4. le **corpus de tests** et les assertions du contrat.

Le XSLT et SaxonC ne sont **pas** portables tels quels : Firefox ne sait
nativement que XSLT 1.0, et Saxon-JS (gratuit mais non libre) est exclu
comme dépendance centrale par décision de principe. Pistes ouvertes côté
navigateur : prétransformation hors navigateur, moteur JS libre s'il en
existe un satisfaisant, ou rendu direct type Custom Elements (CETEIcean)
réimplémentant le contrat HTML.

## État actuel du prototype

Le prototype couvre déjà le rendu prose, poésie, théâtre, correspondance,
notes à deux modes, apparat minimal, témoins, images locales relatives,
éléments de transcription, éléments savants communs, tokenisation et
structures fréquentes. Il dispose aussi de diagnostics, d'un résumé
`inspect`, d'un audit empirique des fixtures, de snapshots HTML et d'une
interface desktop PySide6 expérimentale.

Choix notable : **une seule XSLT commune** (`tei-common.xsl`) pour tous les
genres à ce stade. Les profils diffèrent par paramètres et CSS. Le
mécanisme de surcharge par genre (une feuille `drama.xsl` qui importerait
`tei-common.xsl`) reste prévu par le format de profil (champ `xslt`) mais
n'est pas encore nécessaire : aucune différence *structurelle* de rendu ne
l'exige encore.

Décisions éditoriales maintenues dans le contrat HTML : le texte des
variantes n'est jamais perdu (visibilité par CSS) ; un `app` sans `lem`
affiche son premier `rdg` (`tei-rdg-default`) ; la numérotation des vers est
purement CSS ; les notes finales conservent tous leurs attributs pour
permettre les modes futurs.

### Ce qui est stable

- le contrat HTML (classes `tei-*`, `data-tei-*`, fallback `data-tei`)
  et sa synchronisation XSLT ↔ Python testée ;
- la façade `render()`/`inspect_file()` et le format `RenderResult` ;
- le format des profils JSON et le mécanisme CSS ;
- les diagnostics (codes et résumé chiffré) ;
- la chaîne de sécurité (lxml durci, CSP sans script, aucun réseau) ;
- les snapshots et leur procédure de régénération volontaire.

### Ce qui reste expérimental

- l'interface desktop PySide6, plus native mais encore expérimentale ;
- pywebview, conservé comme prototype et fallback historique ;
- les images locales : `src` en URI `file:` absolue vers le dossier source
  — le HTML n'est donc pas déplaçable sans ses sources (un mode « copie
  des médias » reste à décider) ;
- l'heuristique de suggestion de profil (règles volontairement
  grossières, seuil de 10 vers arbitraire) ;
- l'apparat critique (rendu linéaire, pas d'interface) ;
- les éléments TEI savants non encore priorisés, par exemple `sound`,
  `interp`, `interpGrp`, `event`, `relation` et `desc`.

## Comment ajouter un profil

1. Créer `tei_reader/resources/profiles/<nom>.json` :

```json
{
  "name": "mon-profil",
  "description": "Une ligne visible dans tei-reader profiles.",
  "xslt": "tei-common.xsl",
  "params": { "show-pb": "true", "note-mode": "end" },
  "css": ["base.css", "mon-profil.css"]
}
```

2. Créer les CSS citées dans `tei_reader/resources/css/` (ne cibler que
   les classes et attributs du contrat HTML) ;
3. `tei-reader profiles` doit lister le profil ;
   `tests/test_etape1.py::test_all_profiles_are_valid` vérifie
   automatiquement l'existence des XSLT et CSS de tous les profils ;
4. Une XSLT dédiée n'est justifiée que si la *structure* HTML change ;
   elle importera alors `tei-common.xsl` (champ `xslt` du profil).

## Étapes suivantes envisagées

- notes marginales flottantes (mode `margin`) ;
- mode « copie des médias » à côté du HTML (sorties déplaçables) ;
- cascade de réglages (défauts globaux → profil → corpus → fichier) ;
- vraie interface d'apparat critique ;
- réglages fins par corpus ou fichier dans l'interface ;
- isolation sous-processus du moteur si nécessaire ;
- test de performance sur de très gros fichiers ;
- packaging exécutable ;
- installation QtWebEngine et packaging de l'interface PySide6 ;
- portabilité future vers Firefox.
