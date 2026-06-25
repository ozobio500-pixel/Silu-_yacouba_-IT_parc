/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class ItParcDashboard extends Component {
    static template = "it_parc.Dashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            total_equipment: 0,
            assigned_equipment: 0,
            maintenance_equipment: 0,
            retired_equipment: 0,
            expiring_contracts: 0,
            service_requests: 0,
            active_alerts: 0,
            by_category: {},
            chartSeries: [],
        });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        const data = await this.orm.call("it.parc.dashboard", "get_dashboard_data", [], {});
        Object.assign(this.state, data);
        const maxVal = Math.max(
            data.assigned_equipment,
            data.maintenance_equipment,
            data.retired_equipment,
            1,
        );
        this.state.chartSeries = [
            { label: "Affectés", value: data.assigned_equipment, pct: (data.assigned_equipment / maxVal) * 100 },
            { label: "Maintenance", value: data.maintenance_equipment, pct: (data.maintenance_equipment / maxVal) * 100 },
            { label: "Retirés", value: data.retired_equipment, pct: (data.retired_equipment / maxVal) * 100 },
        ];
    }

    async openEquipment(stateFilter) {
        const domain = stateFilter ? [[["state", "=", stateFilter]]] : [];
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Équipements",
            res_model: "it.parc.equipment",
            view_mode: "list,form",
            domain: stateFilter ? [["state", "=", stateFilter]] : [],
            views: [[false, "list"], [false, "form"]],
        });
    }

    async openContracts() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Contrats expirants",
            res_model: "it.parc.contract",
            view_mode: "list,form",
            domain: [["end_date", "<=", new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]], ["state", "in", ["active", "renewed"]]],
            views: [[false, "list"], [false, "form"]],
            context: {},
        });
    }

    async openInterventions() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Interventions planifiées",
            res_model: "it.parc.intervention",
            view_mode: "calendar,list,form",
            domain: [["status", "=", "planned"]],
            views: [[false, "calendar"], [false, "list"], [false, "form"]],
        });
    }

    async openAlertes() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Alertes actives",
            res_model: "it.alerte",
            view_mode: "list,form",
            domain: [["state", "=", "active"]],
            views: [[false, "list"], [false, "form"]],
        });
    }

    get categoryEntries() {
        return Object.entries(this.state.by_category || {});
    }
}

registry.category("actions").add("it_parc.dashboard", ItParcDashboard);
