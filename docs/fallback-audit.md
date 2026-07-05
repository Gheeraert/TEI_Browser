# Audit des fallbacks sur fixtures réelles

Ce rapport est généré par `python scripts/audit_fixtures.py fixtures`.
Il mesure les éléments TEI encore rendus par le fallback, sans modifier le rendu.

## Résumé

- Dossier audité : `fixtures`
- Fichiers XML : 8
- Fichiers lisibles : 8
- Éléments TEI distincts : 179
- Occurrences TEI : 88540
- Éléments non traités distincts : 31
- Occurrences non traitées : 77466

## Éléments TEI rencontrés

| Élément | Occurrences |
|---|---:|
| `w` | 35416 |
| `c` | 29979 |
| `pc` | 6258 |
| `milestone` | 4669 |
| `lb` | 2746 |
| `p` | 2074 |
| `l` | 1936 |
| `sp` | 1010 |
| `speaker` | 1008 |
| `ab` | 808 |
| `hi` | 445 |
| `stage` | 248 |
| `ptr` | 224 |
| `div2` | 166 |
| `pb` | 136 |
| `div` | 84 |
| `gi` | 76 |
| `fw` | 74 |
| `head` | 59 |
| `att` | 57 |
| `persName` | 52 |
| `tagUsage` | 46 |
| `title` | 43 |
| `q` | 42 |
| `note` | 38 |
| `change` | 38 |
| `person` | 33 |
| `val` | 26 |
| `name` | 24 |
| `date` | 22 |
| `ref` | 19 |
| `seg` | 18 |
| `author` | 16 |
| `sex` | 16 |
| `app` | 16 |
| `rdg` | 16 |
| `bibl` | 15 |
| `addrLine` | 15 |
| `lg` | 15 |
| `sound` | 15 |
| `idno` | 14 |
| `desc` | 14 |
| `add` | 14 |
| `publisher` | 13 |
| `editor` | 13 |
| `del` | 13 |
| `castItem` | 12 |
| `role` | 12 |
| `graphic` | 12 |
| `item` | 12 |
| `respStmt` | 11 |
| `resp` | 11 |
| `state` | 11 |
| `interp` | 11 |
| `language` | 10 |
| `pubPlace` | 9 |
| `term` | 9 |
| `TEI` | 8 |
| `teiHeader` | 8 |
| `fileDesc` | 8 |
| `titleStmt` | 8 |
| `publicationStmt` | 8 |
| `sourceDesc` | 8 |
| `text` | 8 |
| `body` | 8 |
| `availability` | 8 |
| `listPerson` | 8 |
| `subst` | 8 |
| `biblScope` | 7 |
| `measure` | 7 |
| `profileDesc` | 7 |
| `revisionDesc` | 7 |
| `div1` | 7 |
| `licence` | 6 |
| `prefixDef` | 6 |
| `witness` | 6 |
| `principal` | 5 |
| `encodingDesc` | 5 |
| `langUsage` | 5 |
| `surname` | 4 |
| `forename` | 4 |
| `address` | 4 |
| `front` | 4 |
| `sponsor` | 4 |
| `refsDecl` | 4 |
| `quote` | 4 |
| `extent` | 3 |
| `textClass` | 3 |
| `keywords` | 3 |
| `closer` | 3 |
| `signed` | 3 |
| `particDesc` | 3 |
| `funder` | 3 |
| `biblStruct` | 3 |
| `monogr` | 3 |
| `imprint` | 3 |
| `editionStmt` | 3 |
| `edition` | 3 |
| `back` | 3 |
| `metDecl` | 3 |
| `interpGrp` | 3 |
| `notesStmt` | 2 |
| `listBibl` | 2 |
| `correspAction` | 2 |
| `opener` | 2 |
| `salute` | 2 |
| `event` | 2 |
| `titlePart` | 2 |
| `authority` | 2 |
| `refState` | 2 |
| `distributor` | 2 |
| `delSpan` | 2 |
| `unclear` | 2 |
| `anchor` | 2 |
| `location` | 2 |
| `placeName` | 2 |
| `settlement` | 2 |
| `metSym` | 2 |
| `seriesStmt` | 2 |
| `listWit` | 2 |
| `projectDesc` | 2 |
| `editorialDecl` | 2 |
| `correction` | 2 |
| `quotation` | 2 |
| `hyphenation` | 2 |
| `segmentation` | 2 |
| `interpretation` | 2 |
| `tagsDecl` | 2 |
| `namespace` | 2 |
| `variantEncoding` | 2 |
| `citedRange` | 2 |
| `list` | 2 |
| `roleName` | 2 |
| `personGrp` | 2 |
| `label` | 2 |
| `relatedItem` | 1 |
| `msDesc` | 1 |
| `msIdentifier` | 1 |
| `institution` | 1 |
| `repository` | 1 |
| `collection` | 1 |
| `physDesc` | 1 |
| `objectDesc` | 1 |
| `supportDesc` | 1 |
| `support` | 1 |
| `objectType` | 1 |
| `material` | 1 |
| `dimensions` | 1 |
| `height` | 1 |
| `width` | 1 |
| `handDesc` | 1 |
| `handNote` | 1 |
| `correspDesc` | 1 |
| `addName` | 1 |
| `dateline` | 1 |
| `classCode` | 1 |
| `listChange` | 1 |
| `standOff` | 1 |
| `listRelation` | 1 |
| `relation` | 1 |
| `listEvent` | 1 |
| `docTitle` | 1 |
| `docDate` | 1 |
| `docAuthor` | 1 |
| `docImprint` | 1 |
| `performance` | 1 |
| `castList` | 1 |
| `cRefPattern` | 1 |
| `orgName` | 1 |
| `alt` | 1 |
| `choice` | 1 |
| `orig` | 1 |
| `reg` | 1 |
| `textDesc` | 1 |
| `birth` | 1 |
| `country` | 1 |
| `bloc` | 1 |
| `death` | 1 |
| `listPrefixDef` | 1 |

## Éléments non traités par fréquence

| Élément | Occurrences |
|---|---:|
| `w` | 35416 |
| `c` | 29979 |
| `pc` | 6258 |
| `milestone` | 4669 |
| `ab` | 808 |
| `div2` | 166 |
| `fw` | 74 |
| `seg` | 18 |
| `sound` | 15 |
| `desc` | 14 |
| `interp` | 11 |
| `div1` | 7 |
| `bibl` | 4 |
| `interpGrp` | 3 |
| `author` | 2 |
| `event` | 2 |
| `titlePart` | 2 |
| `delSpan` | 2 |
| `anchor` | 2 |
| `citedRange` | 2 |
| `label` | 2 |
| `listRelation` | 1 |
| `relation` | 1 |
| `listEvent` | 1 |
| `docTitle` | 1 |
| `docDate` | 1 |
| `docAuthor` | 1 |
| `docImprint` | 1 |
| `performance` | 1 |
| `alt` | 1 |
| `pubPlace` | 1 |

## Profils suggérés par fichier

| Fichier | Profil suggéré | Raison |
|---|---:|---|
| `fixtures/correspondence/lettre proust.xml` | `correspondence` | présence de <opener>/<closer> |
| `fixtures/drama/corneillep-cid.xml` | `drama` | présence de <sp>/<speaker> |
| `fixtures/greek/tlg0284.tlg048.perseus-grc2.xml` | `prose` | aucun marqueur de genre détecté |
| `fixtures/manuscript/uva.00058.xml` | `verse` | présence de <lg> |
| `fixtures/novel/FRA00502_Balzac.xml` | `prose` | aucun marqueur de genre détecté |
| `fixtures/poetry/Cervantes_de_Salazar,_Francisco_o_Juan__379g~~Soneto__0849.xml` | `verse` | présence de <lg> |
| `fixtures/poetry/Son.xml` | `correspondence` | présence de <opener>/<closer> |
| `fixtures/poetry/Tmp.xml` | `drama` | présence de <sp>/<speaker> |

## Éléments non traités par fichier

| Fichier | Occurrences | Éléments |
|---|---:|---|
| `fixtures/correspondence/lettre proust.xml` | 2 | `bibl` × 1, `author` × 1 |
| `fixtures/drama/corneillep-cid.xml` | 17 | `ab` × 3, `event` × 2, `desc` × 2, `titlePart` × 2, `listRelation` × 1, `relation` × 1, `listEvent` × 1, `docTitle` × 1, `docDate` × 1, `docAuthor` × 1, `docImprint` × 1, `performance` × 1 |
| `fixtures/greek/tlg0284.tlg048.perseus-grc2.xml` | 0 | — |
| `fixtures/manuscript/uva.00058.xml` | 8 | `milestone` × 2, `delSpan` × 2, `anchor` × 2, `seg` × 1, `alt` × 1 |
| `fixtures/novel/FRA00502_Balzac.xml` | 0 | — |
| `fixtures/poetry/Cervantes_de_Salazar,_Francisco_o_Juan__379g~~Soneto__0849.xml` | 0 | — |
| `fixtures/poetry/Son.xml` | 38405 | `w` × 17747, `c` × 15561, `pc` × 2584, `milestone` × 2183, `ab` × 157, `div2` × 156, `desc` × 6, `bibl` × 3, `seg` × 2, `div1` × 2, `citedRange` × 2, `author` × 1, `pubPlace` × 1 |
| `fixtures/poetry/Tmp.xml` | 39034 | `w` × 17669, `c` × 14418, `pc` × 3674, `milestone` × 2484, `ab` × 648, `fw` × 74, `seg` × 15, `sound` × 15, `interp` × 11, `div2` × 10, `desc` × 6, `div1` × 5, `interpGrp` × 3, `label` × 2 |

## Diagnostics importants

| Fichier | Références cassées | Médias manquants |
|---|---|---|
| `fixtures/correspondence/lettre proust.xml` | @corresp="#Lettres" sur <bibl><br>@corresp="#Kolb" sur <bibl><br>@ref="#proust1" sur <persName><br>@ref="#lauris1" sur <persName><br>@ref="#nogret1" sur <persName><br>@ref="#plante2" sur <persName><br>@target="#cp01978" sur <ref><br>@target="#cp01985" sur <ref><br>@ref="#plante1" sur <persName><br>@ref="#fould0" sur <persName><br>@ref="#fould6" sur <persName><br>@target="#cp01223" sur <ref><br>@ref="#fould2" sur <persName><br>@target="#cp01999" sur <ref><br>@target="#cp02003" sur <ref> | <pb> → pas_image.jpg |
| `fixtures/drama/corneillep-cid.xml` | @corresp="#un-page" sur <role> | — |
| `fixtures/greek/tlg0284.tlg048.perseus-grc2.xml` | — | — |
| `fixtures/manuscript/uva.00058.xml` | — | <pb> → uva.00058.001.jpg<br><pb> → uva_jc.00099.jpg |
| `fixtures/novel/FRA00502_Balzac.xml` | — | — |
| `fixtures/poetry/Cervantes_de_Salazar,_Francisco_o_Juan__379g~~Soneto__0849.xml` | — | — |
| `fixtures/poetry/Son.xml` | @ana="#emend" sur <ptr> | <graphic> → fdt-textb-l.png<br><graphic> → fdt-textb-r.png<br><graphic> → fdt-emend-l.png<br><graphic> → fdt-emend-r.png<br><graphic> → fdt-texta-l.png<br><graphic> → fdt-texta-r.png |
| `fixtures/poetry/Tmp.xml` | — | <graphic> → fdt-textb-l.png<br><graphic> → fdt-textb-r.png<br><graphic> → fdt-emend-l.png<br><graphic> → fdt-emend-r.png<br><graphic> → fdt-texta-l.png<br><graphic> → fdt-texta-r.png |

## Candidats fréquents à traiter

- `w` : 35416 occurrence(s), 2 fichier(s)
- `c` : 29979 occurrence(s), 2 fichier(s)
- `pc` : 6258 occurrence(s), 2 fichier(s)
- `milestone` : 4669 occurrence(s), 3 fichier(s)
- `ab` : 808 occurrence(s), 3 fichier(s)
- `div2` : 166 occurrence(s), 2 fichier(s)
- `fw` : 74 occurrence(s), 1 fichier(s)
- `seg` : 18 occurrence(s), 3 fichier(s)
- `sound` : 15 occurrence(s), 1 fichier(s)
- `desc` : 14 occurrence(s), 3 fichier(s)
- `interp` : 11 occurrence(s), 1 fichier(s)
- `div1` : 7 occurrence(s), 2 fichier(s)
- `bibl` : 4 occurrence(s), 2 fichier(s)
- `interpGrp` : 3 occurrence(s), 1 fichier(s)
- `author` : 2 occurrence(s), 2 fichier(s)
- `event` : 2 occurrence(s), 1 fichier(s)
- `titlePart` : 2 occurrence(s), 1 fichier(s)
- `delSpan` : 2 occurrence(s), 1 fichier(s)
- `anchor` : 2 occurrence(s), 1 fichier(s)
- `citedRange` : 2 occurrence(s), 1 fichier(s)
- `label` : 2 occurrence(s), 1 fichier(s)
- `listRelation` : 1 occurrence(s), 1 fichier(s)
- `relation` : 1 occurrence(s), 1 fichier(s)
- `listEvent` : 1 occurrence(s), 1 fichier(s)
- `docTitle` : 1 occurrence(s), 1 fichier(s)
