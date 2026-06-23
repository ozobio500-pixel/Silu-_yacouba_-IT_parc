# IT Parc — Module Odoo 18 TECHPARK CI

Module de gestion du parc informatique pour **TECHPARK CI** (Abidjan).

## Fonctionnalités

- **Équipements** : inventaire complet (série, valeur d'achat, garantie, workflow 4 étapes)
- **Affectations** : liaison employé / département, historique, wizard de réaffectation
- **Interventions** : maintenance corrective/préventive, coût, durée auto, vue calendrier
- **Contrats fournisseurs** : suivi, jours restants, wizard de renouvellement
- **Alertes** (`it.alerte`) : scan automatique (cron) et manuel, délai paramétrable
- **Import CSV** : création en masse, détection doublons, rapport détaillé
- **Rapports PDF** : fiche équipement, inventaire filtrable, historique maintenances
- **Exports Excel** : inventaire complet, coûts maintenance, contrats expirant (60j)
- **Dashboard OWL** : KPIs temps réel + graphiques (composant OWL 2)

## Prérequis

- Odoo 18 Enterprise (ou Community avec modules dépendants)
- Python 3.11+
- `pip install xlsxwriter`

## Installation

1. Copier le dossier `it_parc` dans le répertoire `addons` de votre instance Odoo.
2. Installer la dépendance Python :
   ```bash
   pip install xlsxwriter
   ```
3. Redémarrer Odoo et mettre à jour la liste des applications.
4. Installer le module :
   ```bash
   odoo -d votre_base -i it_parc --without-demo=all
   ```
   Avec données de démo :
   ```bash
   odoo -d votre_base -i it_parc
   ```
5. Mettre à jour le module :
   ```bash
   odoo -d votre_base -u it_parc
   ```

## Groupes de sécurité

| Groupe | Droits |
|--------|--------|
| **IT Technicien** | Lecture équipements/alertes, création/modification interventions |
| **IT Manager** | Accès complet (équipements, contrats, imports, exports, réaffectations) |

Attribuer les groupes via **Paramètres → Utilisateurs**.

## Configuration des alertes

**Paramètres → IT Parc → Délai d'alerte avant expiration** (défaut : 30 jours).

Le scan automatique s'exécute quotidiennement via `ir.cron`. Un scan manuel est disponible dans **IT Parc → Scan alertes**.

## Import CSV

Menu **IT Parc → Import CSV**. Colonnes supportées :

`name`, `serial_no`, `model`, `category`, `site`, `purchase_date`, `purchase_value`, `warranty_end_date`

Un fichier exemple est fourni dans `data/sample_import_equipements.csv`.

## Structure du module

```
it_parc/
├── models/          # Modèles métier (équipement, intervention, contrat, alerte…)
├── views/           # Vues XML, menus, actions
├── wizards/         # Assistants (import, réaffectation, rapports, scan alertes)
├── reports/         # Rapports PDF QWeb
├── security/        # Groupes, ir.model.access.csv, ir.rule
├── data/            # Séquences, crons, démo
└── static/          # Dashboard OWL (JS, XML, SCSS)
```

## Données de démo

Le fichier `data/it_parc_demo.xml` fournit :
- 10 équipements
- 3 contrats fournisseurs
- 5 interventions
- 3 départements et 3 employés

## Auteur

TECHPARK CI — DSI — Juin 2026
