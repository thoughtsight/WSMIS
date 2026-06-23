# WSMIS Dashboard Framework Architecture (Final)

## 1. Framework Diagram

`mermaid
graph TD
    App[app.py / Router] --> Registry[DashboardRegistry]
    Registry --> Controller[DashboardController Base]
    
    subgraph Core Engine Lifecycle
        Controller --> BeforeRender[before_render hook]
        BeforeRender --> FilterEngine[_apply_filters]
        FilterEngine --> MetricEngine[_build_context]
        MetricEngine --> RenderEngine[UI Renders]
        RenderEngine --> BeforeExport[before_export hook]
        BeforeExport --> ExportEngine[_render_exports]
        ExportEngine --> AfterExport[after_export hook]
        AfterExport --> AfterRender[after_render hook]
    end
    
    subgraph Context Payload (Typed & Immutable)
        MetricEngine -.-> |Constructs| Ctx[DashboardContext]
        Ctx -.-> |Contains| M[DashboardMetrics]
        Ctx -.-> |Contains| F[DashboardFilters]
        Ctx -.-> |Contains| C[DashboardConfig]
        Ctx -.-> |Contains| Cap[DashboardCapabilities]
    end
`

## 2. Component Relationship Diagram

`mermaid
graph LR
    Controller[DashboardController] --> UI[UI Renderers]
    UI --> KPI[KPIGrid]
    UI --> Chart[ChartCard]
    UI --> Table[TableCard]
    
    KPI --> Tokens[ui.design_tokens]
    Chart --> Tokens
    Table --> Tokens
`

## 3. Extension Points & Lifecycle
The framework is fully typed via dataclasses.
efore_render() and fter_export() hooks natively support AI and Telemetry injection without modifying individual dashboards.
