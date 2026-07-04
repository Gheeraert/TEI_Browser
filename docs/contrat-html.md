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
   `rend`, `wit`, `target`, `url`, `who`, `met`, `part`.
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
| `pb` | `<span class="tei-pb" data-tei-n data-tei-facs>` | vide ; marqueur « — p. n — » en CSS ; masquable par le paramètre `show-pb` |

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

### Fac-similés

| TEI | HTML | Notes |
|---|---|---|
| `graphic` | `<span class="tei-graphic" data-tei-url>[image : url]</span>` | marqueur seulement (décision étape 1) |

Les chemins locaux de `graphic/@url` et `pb/@facs` sont vérifiés côté
Python : un fichier introuvable produit le diagnostic `missing-media`.

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

## Évolutions prévues du contrat

Classes **réservées** pour les étapes ultérieures : `tei-opener`,
`tei-closer`, `tei-dateline`, `tei-salute`, `tei-signed`
(correspondance) ; `tei-figure`, `tei-surface` (fac-similés avancés).
Toute évolution du rendu de `app`/`rdg` et de `graphic` devra rester
compatible avec les attributs `data-tei-*` déjà émis. Le mode de notes
`margin` (marginales flottantes) viendra s'ajouter à `inline`/`end`
sans les modifier.
