"""Interfaz grafica Streamlit para el Sistema de Diagnostico DGA.

Uso:
    streamlit run main_ui.py

Requiere que la API FastAPI este corriendo en http://127.0.0.1:8000
    fastapi dev main_api.py --port 8000
"""

from __future__ import annotations

import httpx
import streamlit as st
import pandas as pd

API = "http://127.0.0.1:8000"


# ──────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────


def api_get(path: str, **kwargs):
    """GET request a la API. Retorna JSON o None si falla."""
    try:
        r = httpx.get(f"{API}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def api_post(path: str, **kwargs):
    try:
        r = httpx.post(f"{API}{path}", timeout=60, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"Error {e.response.status_code}: {detail}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def api_put(path: str, **kwargs):
    try:
        r = httpx.put(f"{API}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"Error {e.response.status_code}: {detail}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def api_delete(path: str):
    try:
        r = httpx.delete(f"{API}{path}", timeout=30)
        r.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def api_get_image(path: str) -> bytes | None:
    """GET que retorna bytes de una imagen PNG."""
    try:
        r = httpx.get(f"{API}{path}", timeout=60)
        r.raise_for_status()
        return r.content
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:200]
        st.error(f"Error {e.response.status_code}: {detail}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ──────────────────────────────────────────────────────────────────
#  Pagina config
# ──────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DGA - Diagnostico de Gases Disueltos",
    page_icon="⚡",
    layout="wide",
)

st.sidebar.title("⚡ Sistema DGA")
page = st.sidebar.radio(
    "Navegacion",
    [
        "🏠 Inicio",
        "🔌 Transformadores",
        "🧪 Muestras",
        "📋 Diagnostico Normativo",
        "🤖 Inteligencia Artificial",
        "🔗 Diagnostico Unificado",
        "📈 Tendencias y Graficos",
        "✅ Validacion",
        "📥 Importar Excel",
    ],
)

# ──────────────────────────────────────────────────────────────────
#  🏠 Inicio
# ──────────────────────────────────────────────────────────────────

if page == "🏠 Inicio":
    st.title("⚡ Sistema de Diagnostico de Gases Disueltos (DGA)")
    st.markdown("""
    Bienvenido al sistema de diagnostico DGA para transformadores de potencia.

    **Funcionalidades:**
    - **6 metodos normativos**: IEEE C57.104, IEC 60599, Rogers, Dornenburg, Duval T1, Duval P1
    - **4 modelos de IA**: Random Forest, SVM, KNN, Gradient Boosting
    - **Diagnostico unificado**: Combina normativo + IA
    - **Tendencias**: Analisis temporal de gases
    - **Validacion cruzada**: Comparacion de modelos y concordancia
    """)

    # Status check
    info = api_get("/")
    if info:
        col1, col2, col3 = st.columns(3)
        col1.metric("API", "✅ Conectada")
        col2.metric("Version", info.get("version", "?"))

        # Count transformers
        transformers = api_get("/api/transformers/")
        if transformers is not None:
            col3.metric("Transformadores", len(transformers))

        ai_status = api_get("/api/ai/status")
        if ai_status:
            st.info(
                f"Modelo IA: {'✅ Entrenado' if ai_status['has_model'] else '❌ No entrenado'}"
            )

# ──────────────────────────────────────────────────────────────────
#  🔌 Transformadores
# ──────────────────────────────────────────────────────────────────

elif page == "🔌 Transformadores":
    st.title("🔌 Transformadores")

    transformers = api_get("/api/transformers/")

    if transformers:
        df = pd.DataFrame(transformers)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No hay transformadores registrados.")

    st.divider()

    # Crear transformador
    st.subheader("Agregar transformador")
    with st.form("create_transformer"):
        name = st.text_input("Nombre del transformador")
        if st.form_submit_button("Crear"):
            if name.strip():
                result = api_post("/api/transformers/", json={"name": name.strip()})
                if result:
                    st.success(f"Transformador '{result['name']}' creado (ID: {result['id']})")
                    st.rerun()
            else:
                st.warning("Ingresa un nombre.")

    # Eliminar transformador
    if transformers:
        st.subheader("Eliminar transformador")
        options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
        selected = st.selectbox("Selecciona transformador", list(options.keys()))
        if st.button("🗑️ Eliminar", type="secondary"):
            if api_delete(f"/api/transformers/{options[selected]}"):
                st.success("Eliminado.")
                st.rerun()

# ──────────────────────────────────────────────────────────────────
#  🧪 Muestras
# ──────────────────────────────────────────────────────────────────

elif page == "🧪 Muestras":
    st.title("🧪 Muestras")

    transformers = api_get("/api/transformers/")
    if not transformers:
        st.info("Primero crea un transformador.")
    else:
        options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
        selected = st.selectbox("Transformador", list(options.keys()))
        tid = options[selected]

        samples = api_get(f"/api/samples/transformer/{tid}")
        if samples:
            rows = []
            for s in samples:
                g = s["gas_reading"]
                rows.append({
                    "ID": s["id"],
                    "Codigo": s["sample_code"],
                    "Fecha extraccion": s["extraction_date"],
                    "H2": g["h2"], "CH4": g["ch4"], "C2H6": g["c2h6"],
                    "C2H4": g["c2h4"], "C2H2": g["c2h2"],
                    "CO": g["co"], "CO2": g["co2"],
                    "O2": g["o2"], "N2": g["n2"],
                })
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("No hay muestras para este transformador.")

        # Crear muestra
        st.divider()
        st.subheader("Agregar muestra")
        with st.form("create_sample"):
            col1, col2 = st.columns(2)
            code = col1.text_input("Codigo de muestra")
            ext_date = col2.date_input("Fecha de extraccion")

            st.markdown("**Gases disueltos (ppm):**")
            gc1, gc2, gc3 = st.columns(3)
            h2 = gc1.number_input("H2", min_value=0.0, value=0.0, step=1.0)
            ch4 = gc1.number_input("CH4", min_value=0.0, value=0.0, step=1.0)
            c2h6 = gc1.number_input("C2H6", min_value=0.0, value=0.0, step=1.0)
            c2h4 = gc2.number_input("C2H4", min_value=0.0, value=0.0, step=1.0)
            c2h2 = gc2.number_input("C2H2", min_value=0.0, value=0.0, step=1.0)
            co = gc2.number_input("CO", min_value=0.0, value=0.0, step=1.0)
            co2 = gc3.number_input("CO2", min_value=0.0, value=0.0, step=1.0)
            o2 = gc3.number_input("O2", min_value=0.0, value=0.0, step=1.0)
            n2 = gc3.number_input("N2", min_value=0.0, value=0.0, step=1.0)

            if st.form_submit_button("Guardar muestra"):
                if not code.strip():
                    st.warning("Ingresa un codigo de muestra.")
                else:
                    payload = {
                        "sample_code": code.strip(),
                        "transformer_id": tid,
                        "extraction_date": str(ext_date),
                        "h2": h2, "ch4": ch4, "c2h6": c2h6,
                        "c2h4": c2h4, "c2h2": c2h2, "co": co,
                        "co2": co2, "o2": o2, "n2": n2,
                    }
                    result = api_post("/api/samples/", json=payload)
                    if result:
                        st.success(f"Muestra '{result['sample_code']}' creada (ID: {result['id']})")
                        st.rerun()

# ──────────────────────────────────────────────────────────────────
#  📋 Diagnostico Normativo
# ──────────────────────────────────────────────────────────────────

elif page == "📋 Diagnostico Normativo":
    st.title("📋 Diagnostico Normativo")

    tab1, tab2 = st.tabs(["Por muestra existente", "Valores manuales"])

    with tab1:
        transformers = api_get("/api/transformers/")
        if transformers:
            options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
            selected = st.selectbox("Transformador", list(options.keys()), key="diag_trans")
            tid = options[selected]
            samples = api_get(f"/api/samples/transformer/{tid}")
            if samples:
                sample_opts = {
                    f"{s['id']} - {s['sample_code']} ({s['extraction_date']})": s["id"]
                    for s in samples
                }
                sel_sample = st.selectbox("Muestra", list(sample_opts.keys()))
                sid = sample_opts[sel_sample]

                if st.button("🔍 Diagnosticar", key="diag_sample"):
                    result = api_get(f"/api/diagnosis/normative/sample/{sid}")
                    if result:
                        st.subheader(f"Consenso: **{result['consensus_fault']}** ({result['agreement_pct']}% acuerdo)")

                        cols = st.columns(3)
                        for i, m in enumerate(result["methods"]):
                            with cols[i % 3]:
                                st.markdown(f"**{m['method_name']}**")
                                st.code(f"{m['fault_type']}: {m['description']}")
            else:
                st.info("No hay muestras. Crea una primero.")
        else:
            st.info("No hay transformadores.")

    with tab2:
        st.markdown("Ingresa las concentraciones de gases (ppm):")
        with st.form("manual_diagnosis"):
            gc1, gc2, gc3 = st.columns(3)
            h2 = gc1.number_input("H2", min_value=0.0, value=100.0, key="dh2")
            ch4 = gc1.number_input("CH4", min_value=0.0, value=50.0, key="dch4")
            c2h6 = gc1.number_input("C2H6", min_value=0.0, value=30.0, key="dc2h6")
            c2h4 = gc2.number_input("C2H4", min_value=0.0, value=200.0, key="dc2h4")
            c2h2 = gc2.number_input("C2H2", min_value=0.0, value=5.0, key="dc2h2")
            co = gc2.number_input("CO", min_value=0.0, value=400.0, key="dco")
            co2 = gc3.number_input("CO2", min_value=0.0, value=3000.0, key="dco2")
            o2 = gc3.number_input("O2", min_value=0.0, value=0.0, key="do2")
            n2 = gc3.number_input("N2", min_value=0.0, value=0.0, key="dn2")

            if st.form_submit_button("🔍 Diagnosticar"):
                data = {
                    "h2": h2, "ch4": ch4, "c2h6": c2h6,
                    "c2h4": c2h4, "c2h2": c2h2, "co": co,
                    "co2": co2, "o2": o2, "n2": n2,
                }
                result = api_post("/api/diagnosis/normative", json=data)
                if result:
                    st.subheader(f"Consenso: **{result['consensus_fault']}** ({result['agreement_pct']}% acuerdo)")

                    # Votes
                    st.markdown("**Votacion:**")
                    vote_df = pd.DataFrame(
                        [{"Falla": k, "Votos": v} for k, v in result["vote_counts"].items()]
                    ).sort_values("Votos", ascending=False)
                    st.bar_chart(vote_df.set_index("Falla"))

                    cols = st.columns(3)
                    for i, m in enumerate(result["methods"]):
                        with cols[i % 3]:
                            st.markdown(f"**{m['method_name']}**")
                            st.code(f"{m['fault_type']}: {m['description']}")

# ──────────────────────────────────────────────────────────────────
#  🤖 Inteligencia Artificial
# ──────────────────────────────────────────────────────────────────

elif page == "🤖 Inteligencia Artificial":
    st.title("🤖 Inteligencia Artificial")

    ai_status = api_get("/api/ai/status")
    if ai_status:
        if ai_status["has_model"]:
            st.success("Modelo entrenado disponible.")
        else:
            st.warning("No hay modelo entrenado.")

    tab1, tab2, tab3 = st.tabs(["Entrenar", "Clasificar", "Evaluar modelos"])

    with tab1:
        st.markdown("Entrena los 4 modelos (Random Forest, SVM, KNN, Gradient Boosting) "
                     "con todas las muestras del repositorio.")
        if st.button("🚀 Entrenar modelos", type="primary"):
            with st.spinner("Entrenando..."):
                result = api_post("/api/ai/train")
            if result:
                st.success(f"Mejor modelo: **{result['best_model']}** "
                           f"(accuracy: {result['best_accuracy']:.4f})")
                models_df = pd.DataFrame(result["models"])
                st.dataframe(models_df, width="stretch", hide_index=True)

    with tab2:
        st.markdown("Clasifica una lectura de gases con el modelo entrenado:")
        with st.form("ai_classify"):
            gc1, gc2, gc3 = st.columns(3)
            h2 = gc1.number_input("H2", min_value=0.0, value=100.0, key="ah2")
            ch4 = gc1.number_input("CH4", min_value=0.0, value=50.0, key="ach4")
            c2h6 = gc1.number_input("C2H6", min_value=0.0, value=30.0, key="ac2h6")
            c2h4 = gc2.number_input("C2H4", min_value=0.0, value=200.0, key="ac2h4")
            c2h2 = gc2.number_input("C2H2", min_value=0.0, value=5.0, key="ac2h2")
            co = gc2.number_input("CO", min_value=0.0, value=400.0, key="aco")
            co2 = gc3.number_input("CO2", min_value=0.0, value=3000.0, key="aco2")
            o2 = gc3.number_input("O2", min_value=0.0, value=0.0, key="ao2")
            n2 = gc3.number_input("N2", min_value=0.0, value=0.0, key="an2")

            if st.form_submit_button("🤖 Clasificar"):
                data = {
                    "h2": h2, "ch4": ch4, "c2h6": c2h6,
                    "c2h4": c2h4, "c2h2": c2h2, "co": co,
                    "co2": co2, "o2": o2, "n2": n2,
                }
                result = api_post("/api/ai/classify", json=data)
                if result:
                    st.subheader(f"Falla predicha: **{result['fault_type']}**")
                    if result.get("probabilities"):
                        prob_df = pd.DataFrame([
                            {"Tipo de falla": k, "Probabilidad": v}
                            for k, v in result["probabilities"].items()
                        ]).sort_values("Probabilidad", ascending=False)
                        st.bar_chart(prob_df.set_index("Tipo de falla"))

    with tab3:
        if st.button("📊 Evaluar todos los modelos"):
            with st.spinner("Evaluando..."):
                results = api_get("/api/ai/evaluate")
            if results:
                eval_df = pd.DataFrame(results)
                st.dataframe(eval_df, width="stretch", hide_index=True)

# ──────────────────────────────────────────────────────────────────
#  🔗 Diagnostico Unificado
# ──────────────────────────────────────────────────────────────────

elif page == "🔗 Diagnostico Unificado":
    st.title("🔗 Diagnostico Unificado (Normativo + IA)")

    transformers = api_get("/api/transformers/")
    if not transformers:
        st.info("No hay transformadores.")
    else:
        options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
        selected = st.selectbox("Transformador", list(options.keys()), key="uni_trans")
        tid = options[selected]

        tab1, tab2, tab3 = st.tabs(["Por muestra", "Lote completo", "Comparacion"])

        with tab1:
            samples = api_get(f"/api/samples/transformer/{tid}")
            if samples:
                sample_opts = {
                    f"{s['id']} - {s['sample_code']} ({s['extraction_date']})": s["id"]
                    for s in samples
                }
                sel_sample = st.selectbox("Muestra", list(sample_opts.keys()), key="uni_sample")
                sid = sample_opts[sel_sample]

                if st.button("🔍 Diagnostico unificado", key="uni_go"):
                    result = api_get(f"/api/unified/sample/{sid}")
                    if result:
                        col1, col2 = st.columns(2)
                        col1.metric("Normativo", result["normative_consensus"],
                                    f"{result['normative_agreement_pct']}% acuerdo")
                        if result.get("ai_fault"):
                            col2.metric("IA", result["ai_fault"],
                                        "✅ Concuerda" if result.get("agree") else "⚠️ Difiere")
                        else:
                            col2.metric("IA", "Sin modelo")

                        st.markdown("**Metodos normativos:**")
                        for m in result["normative_methods"]:
                            st.text(f"  {m['method_name']}: {m['fault_type']} - {m['description']}")
            else:
                st.info("No hay muestras.")

        with tab2:
            if st.button("📦 Diagnosticar lote completo", key="uni_batch"):
                results = api_get(f"/api/unified/batch/transformer/{tid}")
                if results:
                    rows = []
                    for r in results:
                        rows.append({
                            "ID": r["sample_id"],
                            "Codigo": r["sample_code"],
                            "Normativo": r["normative_consensus"],
                            "Acuerdo %": r["normative_agreement_pct"],
                            "IA": r.get("ai_fault", "-"),
                            "Concuerdan": "✅" if r.get("agree") else ("⚠️" if r.get("ai_fault") else "-"),
                        })
                    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

        with tab3:
            if st.button("📊 Comparar normativo vs IA", key="uni_compare"):
                result = api_get(f"/api/unified/compare/transformer/{tid}")
                if result:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total muestras", result["total"])
                    col2.metric("Acuerdos", result["agreements"])
                    col3.metric("Concordancia", f"{result['agreement_pct']}%")

# ──────────────────────────────────────────────────────────────────
#  📈 Tendencias y Graficos
# ──────────────────────────────────────────────────────────────────

elif page == "📈 Tendencias y Graficos":
    st.title("📈 Tendencias y Graficos")

    transformers = api_get("/api/transformers/")
    if not transformers:
        st.info("No hay transformadores.")
    else:
        options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
        selected = st.selectbox("Transformador", list(options.keys()), key="trend_trans")
        tid = options[selected]

        tab1, tab2, tab3 = st.tabs(["Historial de gases", "Triangulo de Duval", "Tasas de cambio"])

        with tab1:
            history = api_get(f"/api/trends/history/{tid}")
            if history:
                # Show trend chart from API
                img = api_get_image(f"/api/charts/trends/{tid}")
                if img:
                    st.image(img, caption="Tendencias de gases disueltos", width="stretch")

                # Individual charts
                img2 = api_get_image(f"/api/charts/trends/{tid}/individual")
                if img2:
                    st.image(img2, caption="Graficos individuales por gas", width="stretch")
            else:
                st.info("No hay datos de historial.")

        with tab2:
            img = api_get_image(f"/api/charts/duval-triangle/transformer/{tid}")
            if img:
                st.image(img, caption="Triangulo de Duval 1", width="stretch")
            else:
                st.info("No se pudo generar el grafico.")

        with tab3:
            rates = api_get(f"/api/trends/rates/{tid}")
            if rates:
                for rate_set in rates:
                    st.subheader(f"Muestra {rate_set['sample_from_id']} → {rate_set['sample_to_id']} "
                                 f"({rate_set['days_between']} dias)")
                    rate_df = pd.DataFrame(rate_set["gas_rates"])
                    st.dataframe(rate_df, width="stretch", hide_index=True)
                    if rate_set["critical_gases"]:
                        st.warning(f"⚠️ Gases criticos: {', '.join(rate_set['critical_gases'])}")
            else:
                st.info("Se necesitan al menos 2 muestras para calcular tasas.")

# ──────────────────────────────────────────────────────────────────
#  ✅ Validacion
# ──────────────────────────────────────────────────────────────────

elif page == "✅ Validacion":
    st.title("✅ Validacion del Sistema")

    tab1, tab2, tab3 = st.tabs(["Dataset", "Modelos", "Concordancia"])

    with tab1:
        summary = api_get("/api/validation/dataset-summary")
        if summary:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total muestras", summary["total_samples"])
            col2.metric("Transformadores", summary["n_transformers"])
            if summary.get("date_range"):
                col3.metric("Rango fechas", f"{summary['date_range'][0]} a {summary['date_range'][1]}")

            st.subheader("Distribucion de fallas")
            fault_df = pd.DataFrame([
                {"Tipo": k, "Cantidad": v}
                for k, v in summary["fault_distribution"].items()
            ])
            if not fault_df.empty:
                st.bar_chart(fault_df.set_index("Tipo"))

            st.subheader("Estadisticas de gases")
            if summary.get("gas_stats"):
                st.dataframe(pd.DataFrame(summary["gas_stats"]), width="stretch", hide_index=True)

    with tab2:
        if st.button("📊 Comparar modelos", key="val_models"):
            with st.spinner("Evaluando modelos..."):
                result = api_get("/api/validation/model-comparison")
            if result:
                st.dataframe(pd.DataFrame(result), width="stretch", hide_index=True)

                # Charts
                col1, col2 = st.columns(2)
                img1 = api_get_image("/api/charts/model-comparison")
                if img1:
                    col1.image(img1, caption="Comparacion de modelos")
                img2 = api_get_image("/api/charts/class-metrics")
                if img2:
                    col2.image(img2, caption="Metricas por clase")

    with tab3:
        transformers = api_get("/api/transformers/")
        if transformers:
            options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
            selected = st.selectbox("Transformador", list(options.keys()), key="val_trans")
            tid = options[selected]

            if st.button("🔍 Concordancia normativo vs IA", key="val_conc"):
                result = api_get(f"/api/validation/concordance/transformer/{tid}")
                if result:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total", result["total"])
                    col2.metric("Acuerdos", result["agreements"])
                    col3.metric("Concordancia", f"{result['agreement_pct']}%")

# ──────────────────────────────────────────────────────────────────
#  📥 Importar Excel
# ──────────────────────────────────────────────────────────────────

elif page == "📥 Importar Excel":
    st.title("📥 Importar muestras desde Excel")

    transformers = api_get("/api/transformers/")
    if not transformers:
        st.info("Primero crea un transformador.")
    else:
        options = {f"{t['id']} - {t['name']}": t["id"] for t in transformers}
        selected = st.selectbox("Transformador destino", list(options.keys()), key="imp_trans")
        tid = options[selected]

        uploaded = st.file_uploader("Archivo Excel (.xlsx)", type=["xlsx"])
        if uploaded and st.button("📥 Importar", type="primary"):
            with st.spinner("Importando..."):
                try:
                    r = httpx.post(
                        f"{API}/api/import/{tid}",
                        files={"file": (uploaded.name, uploaded.getvalue(),
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                        timeout=60,
                    )
                    r.raise_for_status()
                    result = r.json()
                    st.success(
                        f"Importadas: {result['imported']} de {result['total_rows']} filas. "
                        f"Omitidas: {result['skipped']}"
                    )
                    if result.get("errors"):
                        with st.expander("Errores"):
                            for err in result["errors"]:
                                st.text(err)
                except httpx.HTTPStatusError as e:
                    st.error(f"Error {e.response.status_code}: {e.response.text[:300]}")
                except Exception as e:
                    st.error(f"Error: {e}")
