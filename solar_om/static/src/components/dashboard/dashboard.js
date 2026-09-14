/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Component, useState, onWillStart, useRef, useEffect } from "@odoo/owl";

export class SolarOMDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.cleaningChartRef = useRef("cleaningChart");
        this.completionChartRef = useRef("completionChart");
        this.engineerChartRef = useRef("engineerChart");

        this.state = useState({
            kpis: {},
            cleaning_stats: {},
            task_completion: {},
            engineer_performance: {},
            recent_activities: [],
        });

        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            await this.fetchData();
        });

        useEffect(() => {
            this.renderCharts();
        });
    }

    async fetchData() {
        const data = await this.orm.call("solar.plant", "get_dashboard_data", []);
        this.state.kpis = data.kpis || {};
        this.state.cleaning_stats = data.cleaning_stats || {};
        this.state.task_completion = data.task_completion || {};
        this.state.engineer_performance = data.engineer_performance || {};
        this.state.recent_activities = data.recent_activities || [];
    }

    renderCharts() {
        if (this.cleaningChart) this.cleaningChart.destroy();
        if (this.completionChart) this.completionChart.destroy();
        if (this.engineerChart) this.engineerChart.destroy();

        const cleanCtx = this.cleaningChartRef.el;
        if (cleanCtx) {
            this.cleaningChart = new Chart(cleanCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Draft', 'Assigned', 'In Progress', 'Completed'],
                    datasets: [{
                        data: [
                            this.state.cleaning_stats.draft || 0,
                            this.state.cleaning_stats.assigned || 0,
                            this.state.cleaning_stats.in_progress || 0,
                            this.state.cleaning_stats.completed || 0
                        ],
                        backgroundColor: ['#6c757d', '#17a2b8', '#ffc107', '#28a745'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        }

        const compCtx = this.completionChartRef.el;
        if (compCtx && this.state.task_completion.labels && this.state.task_completion.labels.length) {
            this.completionChart = new Chart(compCtx, {
                type: 'bar',
                data: {
                    labels: this.state.task_completion.labels,
                    datasets: [
                        {
                            label: 'Estimated Hours',
                            data: this.state.task_completion.estimated,
                            backgroundColor: '#007bff',
                        },
                        {
                            label: 'Actual Hours',
                            data: this.state.task_completion.actual,
                            backgroundColor: '#28a745',
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        const engCtx = this.engineerChartRef.el;
        if (engCtx && this.state.engineer_performance.labels && this.state.engineer_performance.labels.length) {
            this.engineerChart = new Chart(engCtx, {
                type: 'bar',
                data: {
                    labels: this.state.engineer_performance.labels,
                    datasets: [{
                        label: 'Tasks Completed',
                        data: this.state.engineer_performance.data,
                        backgroundColor: '#6f42c1',
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    openPlants() {
        this.actionService.doAction("solar_om.action_solar_plant");
    }

    openMaintenance() {
        this.actionService.doAction("solar_om.action_solar_maintenance");
    }

    openBreakdowns() {
        this.actionService.doAction("solar_om.action_solar_breakdown");
    }

    openCleaning() {
        this.actionService.doAction("solar_om.action_solar_cleaning");
    }

    openTasks() {
        this.actionService.doAction("solar_om.action_solar_task");
    }
}

SolarOMDashboard.template = "solar_om.SolarOMDashboard";

registry.category("actions").add("solar_om_dashboard", SolarOMDashboard);
