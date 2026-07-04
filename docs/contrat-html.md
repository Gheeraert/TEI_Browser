# Contrat de rendu HTML

Ce document est la **spécification centrale du projet** : il décrit le HTML
que toute implémentation du lecteur (XSLT aujourd'hui, JavaScript demain
dans une extension navigateur) doit produire à partir du TEI. Les CSS et
les tests s'appuient sur ce contrat, pas sur l'implémentation.

Implémentation actuelle : `tei_reader/resources/xsl/tei-common.xsl`.
Liste des éléments traités, côté Python : `HANDLED_ELEMENTS` dans
`tei_reader/core/document.py` (**à maintenir synchronisés**).

## Règles générales

1. Tout élément TEI rendu porte la classe `tei-<nomLocal>`
   (ex. `<p>` TEI → `<p class="tei-p">`).
2. `@rend` est décomposé en classes additionnelles `rend-<valeur>`
   (ex. `rend="italic sc"` → classes `rend-italic rend-sc`) **et**
   conservé tel quel dans `data-tei-rend`.
3. `@xml:id` → attribut HTML `id` ; `@xml:lang` → attribut HTML `lang`.
4. Les attributs savants sont conservés en `data-tei-<nom>` :
   `type`, `subtype`, `n`, `place`, `ana`, `ref`, `corresp`, `facs`,
   `rend`, `wit`, `target`, `url`.
5. Le `teiHeader` n'est pas rendu dans le corps ; le premier
   `titleStmt/title` devient le `<title>` du document HTML.
6. Le document produit est du HTML5 autonome, sans JavaScript, avec une
   CSP interdisant tout script (`default-src 'none'`).

## Correspondances élément par élément (étape 0)

| TEI | HTML | Notes |
|---|---|---|
| `TEI`, `teiCorpus` | — | conteneurs, seul `text` est rendu |
| `teiHeader` | — | non rendu (titre extrait) |
| `facsimile`, `standOff` | — | non rendus, signalés en diagnostic |
| `text` | `<main class="tei-text">` | |
| `front`, `body`, `back` | `<div class="tei-front/body/back">` | |
| `div` | `<section class="tei-div">` | `@type` → `data-tei-type` |
| `head` | `<h2>`…`<h6>` `class="tei-head"` | niveau = profondeur des `div` ancêtres + 1, plafonné à 6 |
| `p` | `<p class="tei-p">` | |
| `hi` | `<span class="tei-hi rend-*">` | visuel entièrement en CSS |
| `emph` | `<em class="tei-emph">` | |
| `foreign` | `<span class="tei-foreign" lang="…">` | |
| `quote`, `q` | `<span class="tei-quote/q">` | guillemets ajoutés en CSS |
| `note` | `<span class="tei-note">` | inline à l'étape 0 ; `@place` → `data-tei-place` |
| `lb` | `<br class="tei-lb">` | |
| `pb` | `<span class="tei-pb" data-tei-n="…">` | vide ; marqueur « — p. n — » en CSS ; masquable par le paramètre `show-pb` |
| `lg` | `<div class="tei-lg">` | |
| `l` | `<span class="tei-l">` | `display:block` en CSS |
| `app` | `<span class="tei-app">` | rendu linéaire minimal (décision étape 0) |
| `lem` | `<span class="tei-lem">` | visible par défaut |
| `rdg` | `<span class="tei-rdg" data-tei-wit="…">` | masqué en CSS par défaut, visible en profil diagnostic |
| `graphic` | `<span class="tei-graphic" data-tei-url="…">[image : url]</span>` | marqueur seulement (décision étape 0) |

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
| `doc-title-fallback` | texte | `Document TEI` | titre si le teiHeader n'en fournit pas |

## Évolutions prévues du contrat

Les classes suivantes sont **réservées** pour les étapes ultérieures et ne
doivent pas être utilisées à d'autres fins : `tei-sp`, `tei-speaker`,
`tei-stage` (théâtre) ; `tei-opener`, `tei-closer`, `tei-dateline`,
`tei-salute`, `tei-signed` (correspondance) ; `tei-witness`, `tei-listWit`
(témoins). Toute évolution du rendu de `app`/`rdg` et de `graphic` devra
rester compatible avec les attributs `data-tei-*` déjà émis.
