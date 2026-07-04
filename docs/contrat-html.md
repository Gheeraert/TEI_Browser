# Contrat de rendu HTML

Ce document est la **spécification centrale du projet** : il décrit le HTML
que toute implémentation du lecteur (XSLT aujourd'hui, JavaScript demain
dans une extension navigateur) doit produire à partir du TEI. Les CSS et
les tests s'appuient sur ce contrat, pas sur l'implémentation.
**Il documente ce qui est réellement implémenté**, pas des intentions.

Implémentation actuelle : `tei_reader/resources/xsl/tei-common.xsl`.
Liste des éléments traités, côté Python : `HANDLED_ELEMENTS` dans
`tei_reader/core/document.py`. La synchronisation entre les deux est
**vérifiée automatiquement** par `tests/test_contract_sync.py`.

## Règles générales

1. Tout élément TEI rendu porte la classe `tei-<nomLocal>`
   (ex. `<p>` TEI → `<p class="tei-p">`).
2. `@rend` est décomposé en classes additionnelles `rend-<valeur>`
   (ex. `rend="italic sc"` → classes `rend-italic rend-sc`) **et**
   conservé tel quel dans `data-tei-rend`.
3. `@xml:id` → attribut HTML `id` (conservation directe ; les collisions
   éventuelles relèvent de l'encodage source). `@xml:lang` → `lang`.
4. Les attributs savants sont conservés en **`data-tei-<nom>`** — le
   préfixe `tei` évite toute collision avec des `data-*` d'outillage :
   `type`, `subtype`, `n`, `place`, `ana`, `ref`, `corresp`, `facs`,
   `rend`, `wit`, `target`, `url`, `who`, `met`, `part`, `cert`, `resp`,
   `hand`, `reason`, `extent`, `unit`, `seq`, `instant`, `status`.
5. Le `teiHeader` n'est pas rendu dans le corps ; le premier
   `titleStmt/title` devient le `<title>` du document HTML.
6. Le document produit est du HTML5 autonome, sans JavaScript, avec une
   CSP interdisant tout script (`default-src 'none'`).
7. **Distinction rendu natif / fallback** : un élément rendu nativement
   porte `class="tei-<nom>"` ; un élément passé par le fallback porte
   `class="tei-unhandled"` et son nom dans l'attribut `data-tei`.
   Un sélecteur CSS ou un script peut donc toujours distinguer les deux.

## Correspondances élément par élément

### Structure

| TEI | HTML | Notes |
|---|---|---|
| `TEI`, `teiCorpus` | — | conteneurs, seul `text` est rendu |
| `teiHeader` | — | non rendu (titre extrait) |
| `facsimile`, `standOff` | — | non rendus, signalés en diagnostic |
| `text` | `<main class="tei-text">` | accueille les notes finales en mode `end` |
| `front`, `body`, `back` | `<div class="tei-front/body/back">` | |
| `div` | `<section class="tei-div">` | `@type` → `data-tei-type` (`act`, `scene`, `poem`… ciblés par les CSS de genre) |
| `head` | `<h2>`…`<h6>` `class="tei-head"` | niveau = profondeur des `div` ancêtres + 1, plafonné à 6 |
| `p` | `<p class="tei-p">` | |

### Inline

| TEI | HTML | Notes |
|---|---|---|
| `hi` | `<span class="tei-hi rend-*">` | visuel entièrement en CSS |
| `emph` | `<em class="tei-emph">` | |
| `foreign` | `<span class="tei-foreign" lang="…">` | |
| `quote`, `q` | `<span class="tei-quote/q">` | guillemets ajoutés en CSS |
| `lb` | `<br class="tei-lb">` | |
| `pb` | `<span class="tei-pb" data-tei-n data-tei-facs>` — ou `<a class="tei-pb tei-pb-facs" href="…">` si `@facs` désigne un fichier local existant | vide ; marqueur « — p. n — » en CSS ; masquable par le paramètre `show-pb` ; le lien pointe vers le fac-similé local (URI `file:`) |

### Notes (paramètre `note-mode`)

Deux modes, choisis par profil :

- **`inline`** (profil diagnostic) : la note est rendue sur place —
  `<span class="tei-note" data-tei-type data-tei-place data-tei-n>…</span>`.
- **`end`** (profils prose, verse, drama) : à l'emplacement de la note,
  un appel `<a class="tei-note-ref" href="#note-…" id="noteref-…"><sup>N</sup></a>` ;
  en fin de `<main>`, une section :

```html
<section class="tei-notes">
  <h2 class="tei-notes-head">Notes</h2>
  <ol class="tei-notes-list">
    <li class="tei-note" id="note-…" data-tei-type="…" data-tei-place="…">
      <span class="tei-note-marker">N.</span> contenu
      <a class="tei-note-backlink" href="#noteref-…">↩</a>
    </li>
  </ol>
</section>
```

Le marqueur `N` est `@n` si présent, sinon le rang de la note dans le
`<text>`. Les attributs (`type`, `place`, `n`…) sont conservés sur le
`<li>` : la distinction infrapaginale / marginale reste donc possible en
CSS aux étapes suivantes.

### Poésie

| TEI | HTML | Notes |
|---|---|---|
| `lg` | `<div class="tei-lg" data-tei-type data-tei-met data-tei-n>` | |
| `l` | `<span class="tei-l" data-tei-n data-tei-met data-tei-part>` | `display:block` en CSS ; numéro de vers en marge via `.tei-l[data-tei-n]::before` (verse.css) ; segments `@part="M/F"` en retrait |

Décision : la numérotation des vers est purement CSS (aucun texte de
numéro dans le HTML), donc réglable sans retransformation.

### Théâtre

| TEI | HTML | Notes |
|---|---|---|
| `sp` | `<div class="tei-sp" data-tei-who>` | |
| `speaker` | `<span class="tei-speaker">` | bloc centré via drama.css |
| `stage` | `<span class="tei-stage">` | bloc par défaut, inline quand imbriquée dans `p`/`l` (CSS) |
| `castList` | `<div class="tei-castList">` | |
| `castItem` | `<div class="tei-castItem">` | |
| `role` | `<span class="tei-role">` | son `@xml:id` sert de cible aux `@who` |
| `roleDesc` | `<span class="tei-roleDesc">` | |

Actes et scènes sont des `tei:div` ordinaires : c'est `data-tei-type`
(`act`, `scene`) qui porte la sémantique, ciblé par drama.css.

### Apparat critique et témoins

| TEI | HTML | Notes |
|---|---|---|
| `app` | `<span class="tei-app">` | |
| `lem` | `<span class="tei-lem" data-tei-wit>` | |
| `rdg` | `<span class="tei-rdg" data-tei-wit>` (+ `tei-rdg-default` le cas échéant) | |
| `listWit` | `<div class="tei-listWit">` | |
| `witness` | `<div class="tei-witness" id="…">` | cible des `@wit` |

**Décisions éditoriales (étape 1)** :

1. Le texte des variantes n'est **jamais perdu** : `lem` et tous les
   `rdg` sont toujours émis dans le HTML. Leur *visibilité* est pilotée
   par CSS : base.css masque `.tei-rdg` (lecture courante) ;
   apparatus.css les affiche (profil diagnostic).
2. Si un `app` n'a pas de `lem`, le **premier** `rdg` reçoit la classe
   `tei-rdg-default` et reste visible : le texte courant ne présente
   jamais de lacune. Ce choix (privilégier le premier témoin cité) est
   provisoire et devra être paramétrable dans une vraie interface
   d'apparat.
3. Les sigles de témoins (`@wit`) sont affichés en mode diagnostic via
   CSS (`attr(data-tei-wit)`), jamais insérés dans le texte.

### Transcription et normalisation éditoriale

| TEI | HTML | Notes |
|---|---|---|
| `add` | `<span class="tei-add" data-tei-place data-tei-hand>` | ajout visible, stylé sobrement en CSS |
| `del` | `<span class="tei-del">` | suppression barrée ; le texte n'est pas perdu |
| `subst` | `<span class="tei-subst">` | conteneur d'une substitution, conserve `del` et `add` |
| `choice` | `<span class="tei-choice">` | conteneur d'alternatives éditoriales |
| `orig`, `reg` | `<span class="tei-orig/reg">` | forme originale / régularisée |
| `sic`, `corr` | `<span class="tei-sic/corr">` | forme fautive / corrigée |
| `abbr`, `expan` | `<span class="tei-abbr/expan">` | abréviation / développement |
| `unclear` | `<span class="tei-unclear" data-tei-cert data-tei-resp>` | lecture incertaine |
| `gap` | `<span class="tei-gap" data-tei-reason data-tei-extent data-tei-unit>[lacune]</span>` | marqueur textuel si l'élément est vide |
| `supplied` | `<span class="tei-supplied" data-tei-reason>` | texte restitué, crochets en CSS |

**Décision éditoriale (étape 3)** : le lecteur ne choisit pas
silencieusement entre `orig/reg`, `sic/corr` ou `abbr/expan`. En profil
courant, toutes les formes présentes dans `choice` restent dans le HTML
et sont affichées avec un séparateur sobre. En profil `diagnostic`, les
formes sont étiquetées par CSS (`orig:`, `reg:`, etc.). Une future
interface pourra masquer ou privilégier une forme, mais le contrat
conserve les alternatives et leurs attributs dès maintenant.

### Correspondance

| TEI | HTML | Notes |
|---|---|---|
| `opener` | `<div class="tei-opener">` | en-tête de lettre |
| `closer` | `<div class="tei-closer">` | formule finale |
| `dateline` | `<span class="tei-dateline">` | bloc aligné à droite en CSS |
| `salute` | `<span class="tei-salute">` | bloc en CSS |
| `signed` | `<span class="tei-signed">` | bloc aligné à droite en CSS |
| `address` | `<div class="tei-address">` | suscription |
| `addrLine` | `<span class="tei-addrLine">` | une ligne par `addrLine` (CSS) |

Toute la mise en page (alignements, italiques, encadré de l'adresse)
est dans `correspondence.css` ; le HTML ne porte que la structure.
`postscript` et les éléments fins (`date`, `placeName`…) restent en
fallback lisible à ce stade.

### Fac-similés et images locales

| TEI | HTML | Notes |
|---|---|---|
| `graphic` (fichier local existant) | `<span class="tei-graphic" data-tei-url><img class="tei-graphic-img" src="file:…" alt="url"></span>` | image réellement affichée |
| `graphic` (introuvable ou distant) | `<span class="tei-graphic" data-tei-url>[image : url]</span>` | marqueur textuel |

**Décision (étape 2)** : la XSLT ne sait pas tester l'existence d'un
fichier ; c'est Python (`core/document.py`) qui vérifie uniquement les
chemins relatifs locaux de `graphic/@url` et `pb/@facs`, sans schéma,
relatifs au dossier du fichier TEI source. Les chemins absolus POSIX,
Windows, UNC et les chemins contenant `..` sont rejetés : un média ne
peut être résolu que dans le dossier du TEI ou dans ses sous-dossiers.
Python transmet ensuite à la XSLT les paramètres `existing-media`
(valeurs trouvées sur disque) et `media-base` (dossier du fichier source
en URI `file:`, car le HTML est écrit dans un autre dossier et les chemins
du TEI sont relatifs à la source). Un fichier introuvable produit le
diagnostic `missing-media` ; les références `#id`, les URL distantes, les
URI `file:`, `data:`, `urn:` et les URL protocol-relative (`//…`) sont
ignorées — **aucune ressource distante n'est jamais chargée**.

## Fallback (éléments non prévus)

Tout élément TEI sans correspondance ci-dessus est rendu :

```html
<span class="tei-unhandled" data-tei="nomLocal" …data-tei-*…>contenu</span>
```

- le contenu textuel reste toujours lisible ;
- le nom TEI est conservé dans `data-tei` ;
- `@xml:id`, `@xml:lang`, `@rend` (classes `rend-*`) et les attributs
  savants sont conservés comme pour les éléments connus ;
- un élément hors espace de noms TEI reçoit en plus la classe `non-tei`
  et `data-tei-ns` (l'espace de noms d'origine).

En mode lecture, `tei-unhandled` est visuellement neutre ; le profil
**diagnostic** le surligne et affiche le nom de l'élément.

## Paramètres de transformation

| Paramètre | Valeurs | Défaut | Effet |
|---|---|---|---|
| `css-hrefs` | noms de fichiers séparés par des espaces | `base.css` | feuilles liées dans `<head>` (renseigné automatiquement depuis le profil) |
| `show-pb` | `true` / `false` | `true` | émission ou non des marqueurs de saut de page |
| `note-mode` | `inline` / `end` | `inline` | notes sur place ou regroupées en fin de document |
| `doc-title-fallback` | texte | `Document TEI` | titre si le teiHeader n'en fournit pas |
| `existing-media` | valeurs séparées par des sauts de ligne | vide | médias locaux trouvés sur disque (renseigné automatiquement par Python, jamais par les profils) |
| `media-base` | URI `file:` | vide | dossier du fichier source (renseigné automatiquement par Python) |

## Comment ajouter un nouvel élément TEI au contrat

Cinq gestes, dans cet ordre — les tests refusent tout écart :

1. **Documenter ici** la correspondance TEI → HTML (tableau de la bonne
   section), avant d'implémenter : ce fichier décrit ce qui est
   réellement rendu.
2. **Ajouter le template** dans `tei_reader/resources/xsl/tei-common.xsl`
   en appelant `tei-atts` (classe `tei-<nom>`, `id`, `lang`,
   `data-tei-*` : tout est automatique).
3. **Ajouter le nom** à `HANDLED_ELEMENTS` dans
   `tei_reader/core/document.py` — sinon `tests/test_contract_sync.py`
   échoue (synchronisation XSLT ↔ Python vérifiée automatiquement).
4. **Styler en CSS** (base.css ou CSS de genre) en ne ciblant que les
   classes `tei-*` et attributs `data-tei-*` du contrat.
5. **Tester puis régénérer les snapshots** :
   `python -m pytest`, puis si le HTML produit change volontairement,
   `python tests\update_snapshots.py` et relecture du diff git.

Si l'élément est reconnu mais rendu a minima, l'ajouter aussi à
`RECOGNIZED_MINIMAL` (diagnostic `minimal-rendering`) ; s'il est
détecté mais hors rendu, à `SIGNALED_ONLY` et à la liste des éléments
supprimés de la XSLT.

## Évolutions prévues du contrat

Classes **réservées** pour les étapes ultérieures : `tei-figure`,
`tei-surface` (fac-similés avancés).
Toute évolution du rendu de `app`/`rdg` et de `graphic` devra rester
compatible avec les attributs `data-tei-*` déjà émis. Le mode de notes
`margin` (marginales flottantes) viendra s'ajouter à `inline`/`end`
sans les modifier.
