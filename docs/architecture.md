# Architecture

Ce document décrit les couches du lecteur TEI, les décisions prises et
leurs justifications, pour permettre à tout développeur de reprendre le
projet. Le contrat de rendu HTML est décrit dans [contrat-html.md](contrat-html.md).

## Vue d'ensemble

```
              ┌─────────────────────────────────────────────┐
 interfaces   │  cli.py          ui/webview_app.py   (plus  │
 (aucune      │  (render/view/    (fenêtre WebView2) tard : │
  logique)    │   profiles)                          Flask) │
              └───────────────────┬─────────────────────────┘
                                  │  appelle uniquement
              ┌───────────────────▼─────────────────────────┐
 façade       │  core/service.py : render(fichier, profil,  │
              │  dossier de sortie) -> RenderResult          │
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

### Diagnostics par inventaire lxml, pas par xsl:message

Les éléments non traités sont détectés en Python (comparaison à
`HANDLED_ELEMENTS`) plutôt que par des `xsl:message` interceptés : la
récupération des messages de SaxonC côté Python est fragile, et
l'inventaire lxml fonctionne même si la transformation échoue.
**Contrainte de maintenance** : quand on ajoute un template dans
`tei-common.xsl`, il faut ajouter l'élément à `HANDLED_ELEMENTS` dans
`core/document.py` (et inversement).

### Profils hybrides

Un profil JSON = XSLT d'entrée + paramètres + CSS. Trois niveaux de
personnalisation, du plus courant au plus rare :

1. **CSS** : tout le visuel (italiques, thèmes, visibilité des variantes) ;
2. **paramètres XSLT** : booléens et scalaires (`show-pb`...) ;
3. **surcharge XSLT** : seulement quand la *structure* HTML change
   (futurs `drama.xsl`, `verse.xsl`... qui importeront `tei-common.xsl`).

Les niveaux 1 et 2 ne demandent jamais de toucher au XSLT, et sont
directement portables vers un futur lecteur navigateur.

### Sécurité

- lxml : `resolve_entities=False`, `no_network=True`, `load_dtd=False` —
  le fichier est validé avant tout passage à Saxon.
- HTML produit : CSP `default-src 'none'` (aucun script), styles et images
  limités à `'self'` et au schéma `file:` (`'self'` est inopérant sous
  `file://`, origine opaque).
- Aucun JavaScript n'est généré ni injecté dans le rendu.
- Sorties dans un dossier explicite choisi par l'utilisateur (`--out`),
  pas de fichiers temporaires anonymes : rendu reproductible et inspectable.

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

## Étapes suivantes envisagées (hors étape 0)

- modules XSLT par genre (`verse.xsl`, `drama.xsl`, `letters.xsl`) par
  import/surcharge de `tei-common.xsl`, avec profils JSON associés ;
- cascade de réglages (défauts globaux → profil → corpus → fichier) ;
- vraie interface d'apparat critique et affichage des fac-similés locaux ;
- rechargement à chaud des profils dans l'UI ;
- isolation sous-processus du moteur si nécessaire ;
- tests de non-régression par snapshots HTML normalisés et test de
  performance sur un gros fichier.
