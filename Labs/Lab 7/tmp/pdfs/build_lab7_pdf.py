import base64
import io
import json
from pathlib import Path

from PIL import Image as PILImage, ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).parents[2]
NOTEBOOK = ROOT / "Lab7_Forecasting_ETTh1.ipynb"
TMP = ROOT / "tmp" / "pdfs"
OUT_DIR = ROOT / "output" / "pdf"
PROMPTS = TMP / "prompts.json"
OUT = OUT_DIR / "Lab7_Respuestas_Diego_Lopez_23747.pdf"


def register_fonts():
    fonts = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("DocSans", str(fonts / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("DocSans-Bold", str(fonts / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("DocMono", str(fonts / "consola.ttf")))
    pdfmetrics.registerFontFamily(
        "DocSans", normal="DocSans", bold="DocSans-Bold", italic="DocSans", boldItalic="DocSans-Bold"
    )


register_fonts()

styles = getSampleStyleSheet()
BODY = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName="DocSans",
    fontSize=9.4,
    leading=13.2,
    alignment=TA_JUSTIFY,
    textColor=colors.black,
    spaceAfter=6,
)
H1 = ParagraphStyle(
    "H1",
    parent=BODY,
    fontName="DocSans-Bold",
    fontSize=16,
    leading=19,
    spaceBefore=3,
    spaceAfter=9,
    keepWithNext=True,
)
H2 = ParagraphStyle(
    "H2",
    parent=BODY,
    fontName="DocSans-Bold",
    fontSize=12,
    leading=15,
    spaceBefore=9,
    spaceAfter=5,
    keepWithNext=True,
)
H3 = ParagraphStyle(
    "H3",
    parent=BODY,
    fontName="DocSans-Bold",
    fontSize=10,
    leading=13,
    spaceBefore=6,
    spaceAfter=4,
    keepWithNext=True,
)
BULLET = ParagraphStyle(
    "Bullet",
    parent=BODY,
    leftIndent=14,
    firstLineIndent=-8,
    bulletIndent=5,
    spaceAfter=3,
)
CAPTION = ParagraphStyle(
    "Caption",
    parent=BODY,
    fontSize=8.2,
    leading=10.5,
    alignment=TA_CENTER,
    spaceBefore=3,
    spaceAfter=9,
)
VERIFY = ParagraphStyle(
    "Verify",
    parent=BODY,
    fontName="DocMono",
    fontSize=8.6,
    leading=11.5,
    leftIndent=12,
    rightIndent=12,
    borderWidth=0.5,
    borderColor=colors.black,
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=9,
)
PROMPT = ParagraphStyle(
    "Prompt",
    parent=BODY,
    fontName="DocMono",
    fontSize=8.2,
    leading=11,
    leftIndent=10,
    rightIndent=10,
    borderWidth=0.5,
    borderColor=colors.black,
    borderPadding=6,
    spaceAfter=5,
)


def p(text, style=BODY):
    return Paragraph(text, style)


def bullet(text):
    return Paragraph("• " + text, BULLET)


def table(data, widths, alignments=None, font_size=8.2):
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, 0), "DocSans-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "DocSans"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2.5),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]
    if alignments:
        for col, alignment in enumerate(alignments):
            commands.append(("ALIGN", (col, 1), (col, -1), alignment))
            commands.append(("ALIGN", (col, 0), (col, 0), alignment))
    t.setStyle(TableStyle(commands))
    return t


def extract_figures():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    mapping = {
        9: "fig_1_acf.png",
        21: "fig_2_lstm_loss.png",
        33: "fig_3_heatmaps.png",
        39: "fig_4_acf_atencion.png",
        41: "fig_5_atencion_ejemplos.png",
    }
    paths = {}
    for cell_index, filename in mapping.items():
        encoded = None
        for output in notebook["cells"][cell_index].get("outputs", []):
            encoded = output.get("data", {}).get("image/png")
            if encoded:
                break
        if not encoded:
            raise RuntimeError(f"No se encontro image/png en la celda {cell_index}")
        if isinstance(encoded, list):
            encoded = "".join(encoded)
        image = PILImage.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
        image = ImageOps.grayscale(image)
        path = TMP / filename
        image.save(path, format="PNG", optimize=True)
        paths[cell_index] = path
    return paths


def figure(path, width=7.0 * inch):
    with PILImage.open(path) as im:
        w, h = im.size
    height = width * h / w
    if height > 4.15 * inch:
        height = 4.15 * inch
        width = height * w / h
    return Image(str(path), width=width, height=height, hAlign="CENTER")


def load_prompts():
    if not PROMPTS.exists():
        return {str(i): {"prompt": "[COMPLETAR POR EL USUARIO]", "why": "[COMPLETAR POR EL USUARIO]"} for i in range(1, 5)}
    data = json.loads(PROMPTS.read_text(encoding="utf-8"))
    for i in range(1, 5):
        item = data.get(str(i), {})
        if not item.get("prompt") or not item.get("why"):
            raise ValueError(f"Falta prompt o explicacion para Task {i}")
    return data


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")


def page_decor(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.black)
    canvas.setFont("DocSans", 7.5)
    if doc.page > 1:
        canvas.drawString(doc.leftMargin, letter[1] - 0.42 * inch, "CC3092 - Deep Learning | Laboratorio 7")
        canvas.drawRightString(letter[0] - doc.rightMargin, letter[1] - 0.42 * inch, "Diego Lopez #23747")
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.35)
        canvas.line(doc.leftMargin, letter[1] - 0.49 * inch, letter[0] - doc.rightMargin, letter[1] - 0.49 * inch)
    canvas.drawCentredString(letter[0] / 2, 0.35 * inch, str(doc.page))
    canvas.restoreState()


def build():
    TMP.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    figs = extract_figures()
    prompts = load_prompts()
    story = []

    # Portada
    story += [Spacer(1, 1.45 * inch)]
    story += [p("DEEP LEARNING", ParagraphStyle("CoverKicker", parent=BODY, fontName="DocSans-Bold", fontSize=12, leading=15, alignment=TA_CENTER, spaceAfter=12))]
    story += [p("Laboratorio 7", ParagraphStyle("CoverTitle", parent=BODY, fontName="DocSans-Bold", fontSize=26, leading=31, alignment=TA_CENTER, spaceAfter=8))]
    story += [p("Forecasting de temperatura de aceite con LSTM y Transformer", ParagraphStyle("CoverSub", parent=BODY, fontSize=14, leading=19, alignment=TA_CENTER, spaceAfter=25))]
    story += [HRFlowable(width="55%", thickness=0.8, color=colors.black, spaceBefore=4, spaceAfter=24, hAlign="CENTER")]
    cover_info = [
        ["Autor", "Diego López"],
        ["Carné", "23747"],
        ["Curso", "Deep Learning (CC3092)"],
        ["Sección", "20"],
        ["Fecha de entrega", "27 de septiembre de 2026"],
    ]
    cover = Table(cover_info, colWidths=[1.55 * inch, 3.2 * inch], hAlign="CENTER")
    cover.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "DocSans-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "DocSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("LEADING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.black),
    ]))
    story += [cover, PageBreak()]

    story += [p("Decisiones de diseño", H1)]
    story += [p("El pipeline evita fuga de información y usa la misma configuración experimental para que la comparación entre arquitecturas sea directa.")]
    story += [bullet("Normalización: <i>z</i><sub>t</sub> = (<i>x</i><sub>t</sub> - μ)/σ con μ y σ calculados solo sobre entrenamiento.")]
    story += [bullet("Predicción relativa a <i>x</i><sub>t</sub>: la red recibe <i>X</i> - <i>x</i><sub>t</sub> y aprende <i>y</i> - <i>x</i><sub>t</sub>, debido al cambio de nivel entre train y validación/prueba.")]
    story += [bullet("Pérdida MSE, optimizador Adam, 20 épocas, batch size 64 y learning rate 10<super>-3</super>.")]
    story += [bullet("Ejecución en CPU y semilla 42 para PyTorch y NumPy.")]
    story += [bullet("Un modelo independiente por horizonte H ∈ {24, 48}; ambos son directos y producen una sola salida.")]

    # Task 1
    story += [p("Task 1 - Preprocesamiento y autocorrelación", H1)]
    story += [p("1.1 Normalización, split temporal y ventanas", H2)]
    story += [p("Se descargaron 17,420 observaciones de ETTh1 sin valores NaN. La variable OT se normalizó con estadísticas exclusivas del bloque de entrenamiento y se dividió temporalmente 60/20/20 en bloques contiguos, sin mezcla aleatoria.")]
    story += [table(
        [["Estadística", "Valor"], ["μ de train", "17.2925"], ["σ de train", "8.5137"]],
        [2.2 * inch, 1.5 * inch], ["LEFT", "RIGHT"]
    ), Spacer(1, 6)]
    story += [table(
        [["Split", "Pasos", "Media normalizada", "Desv. estándar"],
         ["Train", "10,452", "+0.000", "1.000"],
         ["Validación", "3,484", "-1.206", "0.516"],
         ["Prueba", "3,484", "-1.124", "0.405"]],
        [1.45 * inch, 1.1 * inch, 1.65 * inch, 1.45 * inch], ["LEFT", "RIGHT", "RIGHT", "RIGHT"]
    ), Spacer(1, 6)]
    story += [p("Cada ejemplo usa una ventana X<super>(t)</super> = (x<sub>t-L+1</sub>, …, x<sub>t</sub>) y objetivo y<super>(t)</super> = x<sub>t+H</sub>. Para una serie de largo T, N = T - L - H + 1.")]
    story += [table(
        [["H", "Split", "Shape de X", "Shape de y"],
         ["24", "Train", "(10,333, 96)", "(10,333,)"],
         ["24", "Validación", "(3,365, 96)", "(3,365,)"],
         ["24", "Prueba", "(3,365, 96)", "(3,365,)"],
         ["48", "Train", "(10,309, 96)", "(10,309,)"],
         ["48", "Validación", "(3,341, 96)", "(3,341,)"],
         ["48", "Prueba", "(3,341, 96)", "(3,341,)"],
        ], [0.55 * inch, 1.25 * inch, 1.55 * inch, 1.45 * inch], ["CENTER", "LEFT", "CENTER", "CENTER"]
    )]

    story += [p("1.2 Función de autocorrelación", H2)]
    story += [p("La ACF se calculó manualmente sobre train para los lags 0 a 96. La banda de confianza al 95% es ±0.0192; toda la ACF observada queda muy por encima de ella.")]
    story += [figure(figs[9]), p("Figura 1. ACF de OT normalizada en entrenamiento, con banda de confianza al 95%.", CAPTION)]
    story += [p("1.2 a. Segundo pico más alto e interpretación", H3)]
    story += [p("El valor más alto después de lag 0 es lag 1 (ρ(1)=0.9923), pero es el inicio del decaimiento y no un pico local. El pico local más alto es lag 22 (ρ=0.9262), prácticamente empatado con lag 24 (ρ(24)=0.9250); después aparecen lag 47 (0.8770) y lag 72 (0.8572). La separación aproximada de 24-25 horas respalda un ciclo diario sobre una componente lenta y persistente.")]
    story += [bullet("ρ(12)=0.9250, ρ(22)=0.9262 y ρ(24)=0.9250: la zona es casi plana, con diferencias menores que 0.002.")]
    story += [bullet("La secuencia de máximos 22 → 47 → 72 confirma una periodicidad cercana a un día.")]
    story += [p("1.2 b. Adecuación de L = 96", H3)]
    story += [p("L = 96 es apropiado porque cubre cuatro ciclos diarios completos. Incluso ρ(96)=0.8489, muy por encima de ±0.0192, por lo que la historia sigue siendo informativa; sin embargo, extender la ventana agregaría principalmente información redundante y elevaría el costo del LSTM y de la atención.")]
    story += [bullet("Una ventana menor que 24 perdería el ciclo diario completo; L=48 conservaría solo dos ciclos.")]
    story += [bullet("De lag 47 a lag 96 la ACF apenas cae de 0.8770 a 0.8489, señal de alta colinealidad.")]
    story += [bullet("Explorar L=168 podría probar el ciclo semanal, pero esta ACF hasta 96 no aporta evidencia para justificarlo.")]
    story += [p("Verificación Task 1", H3), p("Task 1: CORRECTO (ACF lag24=0.9250, naive_mae=0.2009)", VERIFY)]

    # Task 2
    story += [p("Task 2 - LSTM", H1)]
    story += [p("2.1 LSTMForecaster manual", H2)]
    story += [p("La celda LSTM procesa manualmente cada paso, apila las cuatro compuertas y usa el último estado oculto para producir una predicción escalar many-to-one.")]
    story += [p("[i; f; g; o] = x<sub>t</sub> W<sub>x</sub><super>T</super> + h<sub>t-1</sub> W<sub>h</sub><super>T</super> + b; &nbsp; i,f,o = σ(·), &nbsp; g = tanh(·)", VERIFY)]
    story += [p("c<sub>t</sub> = f ⊙ c<sub>t-1</sub> + i ⊙ g; &nbsp; h<sub>t</sub> = o ⊙ tanh(c<sub>t</sub>); &nbsp; ŷ = h<sub>T</sub> W<sub>out</sub><super>T</super> + b<sub>out</sub>", VERIFY)]

    story += [p("2.2 Entrenamiento y evaluación", H2)]
    story += [p("Se entrenó un LSTM distinto por horizonte con d<sub>h</sub>=32. Validación y prueba están aproximadamente 1.2 desviaciones por debajo de train y presentan cerca de la mitad de variabilidad, por lo que se entrenó sobre diferencias respecto del último valor observado x<sub>t</sub>. La predicción final vuelve a nivel absoluto mediante ŷ = x<sub>t</sub> + f(X - x<sub>t</sub>).")] 
    story += [p("La MSE fue elegida por tratarse de regresión continua, penalizar con más fuerza los errores grandes, ofrecer un gradiente suave y ser coherente con el RMSE reportado. El MAE se conserva como métrica interpretable en °C.")]
    story += [table(
        [["Modelo", "H", "MAE", "RMSE", "Ratio", "MAE °C", "RMSE °C"],
         ["LSTM", "24", "0.2040", "0.2694", "1.015", "1.736", "2.294"],
         ["LSTM", "48", "0.2601", "0.3331", "0.993", "2.214", "2.836"],
         ["Naive", "24", "0.2009", "0.2689", "1.000", "1.710", "2.289"],
         ["Naive", "48", "0.2620", "0.3380", "1.000", "2.231", "2.878"]],
        [1.05 * inch, 0.45 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch, 0.85 * inch, 0.9 * inch],
        ["LEFT", "CENTER", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"]
    )]
    story += [p("El LSTM queda prácticamente empatado con naive: en H=24 su MAE es ligeramente peor, mientras que en H=48 lo mejora apenas. Las pérdidas se estabilizan muy pronto; el modelo aprende una corrección pequeña sobre x<sub>t</sub> y deja de mejorar de forma sostenida.")]
    story += [figure(figs[21], 6.65 * inch), p("Figura 2. Curvas de pérdida MSE de entrenamiento del LSTM para H=24 y H=48.", CAPTION)]
    story += [p("Verificación Task 2", H3), p("Task 2: CORRECTO<br/>LSTM H=24: MAE=0.2040, ratio=1.015", VERIFY)]

    # Task 3
    story += [p("Task 3 - Transformer", H1)]
    story += [p("3.1 Positional encoding", H2)]
    story += [p("Cada valor escalar se proyecta a R<super>d_model</super> con una capa lineal y luego se suma un positional encoding sinusoidal no aprendible. El tensor resultante tiene shape (96, 32) y requires_grad=False.")]
    story += [p("PE(t,2i) = sin(t / 10000<super>2i/d_model</super>), &nbsp; PE(t,2i+1) = cos(t / 10000<super>2i/d_model</super>)", VERIFY)]
    story += [p("3.2 Multi-head self-attention, LayerNorm y FFN", H2)]
    story += [p("El encoder implementa manualmente dos cabezas de atención. Tras cada subcapa se aplica conexión residual y normalización; la salida se toma de la posición 0, usada como CLS aunque corresponde al dato más antiguo de la ventana.")]
    story += [p("Q=XW<sub>Q</sub>, K=XW<sub>K</sub>, V=XW<sub>V</sub>; &nbsp; head<sub>h</sub>=softmax(Q<sub>h</sub>K<sub>h</sub><super>T</super>/√d<sub>k</sub>)V<sub>h</sub>", VERIFY)]
    story += [p("MHA(X)=[head<sub>1</sub>;…;head<sub>H</sub>]W<sub>O</sub>; &nbsp; LN(x)=γ⊙(x-μ)/√(σ²+ε)+β; &nbsp; FFN(x)=ReLU(xW<sub>1</sub>+b<sub>1</sub>)W<sub>2</sub>+b<sub>2</sub>", VERIFY)]

    story += [p("3.3 Entrenamiento, evaluación y mapas de atención", H2)]
    story += [p("Se entrenó un Transformer por horizonte con d<sub>model</sub>=32, dos cabezas, d<sub>ff</sub>=64 y las mismas condiciones del LSTM. La tabla muestra las métricas de validación y el baseline naive.")]
    story += [table(
        [["Modelo", "H", "MAE", "RMSE", "Ratio", "MAE °C", "RMSE °C"],
         ["Transformer", "24", "0.2066", "0.2589", "1.029", "1.759", "2.204"],
         ["Transformer", "48", "0.2413", "0.3160", "0.921", "2.055", "2.690"],
         ["Naive", "24", "0.2009", "0.2689", "1.000", "1.710", "2.289"],
         ["Naive", "48", "0.2620", "0.3380", "1.000", "2.231", "2.878"]],
        [1.1 * inch, 0.4 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch, 0.85 * inch, 0.9 * inch],
        ["LEFT", "CENTER", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"]
    )]
    story += [p("Los mapas promedian cinco ventanas de validación y dos cabezas. Para H=24 se usaron los índices [0, 841, 1682, 2523, 3364]; para H=48, [0, 835, 1670, 2505, 3340].")]
    story += [figure(figs[33], 6.8 * inch), p("Figura 3. Mapas de atención promedio para H=24 y H=48.", CAPTION)]
    story += [p("3.3 d. Posiciones con mayor atención desde CLS", H3)]
    story += [p("La atención desde CLS se concentra en bandas lejanas, no en los lags más recientes. Las franjas verticales indican que distintas queries tienden a mirar las mismas keys, por lo que el patrón depende en gran medida de la posición y el contenido de la key.")]
    story += [bullet("H=24: lags 77-81, con máximos en lag 80 (0.1095) y 79 (0.1033); segunda banda en 45-49, con lag 47=0.0473 y lag 48=0.0452.")]
    story += [bullet("H=48: lags 70-74, con lag 73=0.0598 y lag 72=0.0584; también lag 79=0.0458 y lags 45-48 alrededor de 0.03-0.035.")]
    story += [bullet("El peso uniforme sería 1/96=0.0104; lag 1 recibe 0.0002 en H=24 y 0.0013 en H=48.")]
    story += [p("Verificación Task 3", H3), p("Task 3: CORRECTO<br/>attn_w shape: torch.Size([4, 2, 96, 96])<br/>row sums OK: 1.0000 a 1.0000", VERIFY)]

    # Task 4
    story += [p("Task 4 - Comparación e interpretación", H1)]
    story += [p("4.1 ACF frente a atención", H2)]
    story += [p("4.1 a. Coincidencia de los lags", H3)]
    story += [p("Los lags de mayor atención coinciden solo parcialmente con los picos de la ACF. La ACF es máxima en lags cortos y decae, mientras que la atención casi ignora esos lags y privilegia algunas bandas lejanas.")]
    story += [table(
        [["Lag", "ACF", "Atención H=24", "Atención H=48"],
         ["1", "0.9923", "0.0002", "0.0013"],
         ["22 (pico ACF)", "0.9262", "0.0016", "0.0018"],
         ["24", "0.9250", "0.0104", "0.0032"],
         ["47 (pico ACF)", "0.8770", "0.0473", "0.0339"],
         ["48", "0.8763", "0.0452", "0.0298"],
         ["72 (pico ACF)", "0.8572", "0.0079", "0.0584"],
         ["79", "0.8361", "0.1033", "0.0458"],
         ["80", "0.8334", "0.1095", "fuera del top"]],
        [1.55 * inch, 0.9 * inch, 1.3 * inch, 1.3 * inch], ["LEFT", "RIGHT", "RIGHT", "RIGHT"]
    )]
    story += [p("La correlación de Spearman entre los perfiles completos de lags 1-96 es negativa: -0.209 para H=24 y -0.323 para H=48. La coincidencia aparece en lag 47/48 para ambos horizontes y en lag 72 para H=48; la banda 78-81 de H=24 no corresponde a un pico de la ACF.")]
    story += [p("La diferencia es coherente con que la ACF mide redundancia lineal, mientras que el modelo minimiza el MSE del cambio y busca información complementaria. Al centrar en x<sub>t</sub>, los valores recientes aportan poco; los lags 48 y 72 corresponden a una hora del día comparable con el objetivo, y la banda cercana a 80 puede servir como referencia de tendencia de varios días.")]
    story += [figure(figs[39], 6.85 * inch), p("Figura 4. Perfil de ACF frente a atención desde CLS para H=24 y H=48.", CAPTION)]

    story += [p("4.1 b. Dependencias no lineales", H3)]
    story += [p("La ACF asigna un único valor lineal y estacionario a cada lag. En cambio, los scores de atención dependen de proyecciones aprendidas de los valores y pueden variar con el contenido, el régimen y la hora del día; además, la interacción query-key es bilineal y se combina con softmax y una FFN con ReLU.")]
    story += [bullet("El coeficiente de variación medio entre ejemplos es 0.597 para H=24 y 0.606 para H=48.")]
    story += [bullet("En H=48 el lag de máxima atención cambia por ejemplo: [72, 73, 80, 79, 67].")]
    story += [bullet("En H=24 el máximo permanece en 79-80, pero cambian los picos secundarios en torno a 23-28, 45-47 y 68.")]
    story += [p("La evidencia de dependencia condicionada por el contenido existe, aunque es moderada: cinco ejemplos son pocos y las franjas verticales revelan un componente posicional fuerte.")]
    story += [figure(figs[41], 6.85 * inch), p("Figura 5. Atención desde CLS por ejemplo de validación para H=24 y H=48.", CAPTION)]

    story += [p("4.2 Comparación LSTM, Transformer y naive", H2)]
    story += [p("La comparación completa se presenta una sola vez. Todas las métricas corresponden a validación y a la escala normalizada; las dos últimas columnas convierten los errores a grados Celsius.")]
    story += [table(
        [["Modelo", "Horizonte", "MAE", "RMSE", "Ratio vs naive", "MAE °C", "RMSE °C"],
         ["LSTM", "24 h", "0.2040", "0.2694", "1.015", "1.736", "2.294"],
         ["LSTM", "48 h", "0.2601", "0.3331", "0.993", "2.214", "2.836"],
         ["Transformer", "24 h", "0.2066", "0.2589", "1.029", "1.759", "2.204"],
         ["Transformer", "48 h", "0.2413", "0.3160", "0.921", "2.055", "2.690"],
         ["Naive", "24 h", "0.2009", "0.2689", "1.000", "1.710", "2.289"],
         ["Naive", "48 h", "0.2620", "0.3380", "1.000", "2.231", "2.878"]],
        [1.05 * inch, 0.75 * inch, 0.68 * inch, 0.72 * inch, 1.05 * inch, 0.78 * inch, 0.82 * inch],
        ["LEFT", "CENTER", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"], 7.6
    )]
    story += [p("4.2 a. Aumento del error con el horizonte", H3)]
    story += [p("En predicción iterativa, el error se propaga como e<sub>t+h</sub> ≈ ε<sub>t+h</sub> + J e<sub>t+h-1</sub>, de modo que e<sub>t+h</sub> ≈ Σ<super>h-1</super><sub>j=0</sub> J<super>j</super> ε<sub>t+h-j</sub> y Var(e<sub>t+h</sub>) ≈ σ² Σ<super>h-1</super><sub>j=0</sub> J<super>2j</super>. Con ρ(1)=0.99, J≈1 y la acumulación sería casi lineal.")]
    story += [p("Sin embargo, los dos modelos implementados son <b>directos de una sola salida</b>: se entrena un modelo separado para cada H y ninguno realimenta predicciones. El error aumenta por la incertidumbre intrínseca del futuro más lejano. Para un predictor lineal basado solo en x<sub>t</sub>, 1-ρ(H)² vale 0.1445 en H=24 y 0.2320 en H=48, un factor de 1.61.")]
    story += [table(
        [["Modelo", "MSE H=24", "MSE H=48", "Factor"],
         ["Naive", "0.2689² = 0.0723", "0.3380² = 0.1142", "1.58"],
         ["LSTM", "0.0726", "0.1110", "1.53"],
         ["Transformer", "0.0670", "0.0999", "1.49"]],
        [1.25 * inch, 1.45 * inch, 1.45 * inch, 0.85 * inch], ["LEFT", "RIGHT", "RIGHT", "RIGHT"]
    )]
    story += [p("4.2 b. Flujo del gradiente", H3)]
    story += [p("En H=48 el Transformer supera al LSTM (MAE 0.2413 frente a 0.2601; RMSE 0.3160 frente a 0.3331). En H=24 no lo supera en MAE (0.2066 frente a 0.2040), aunque sí en RMSE (0.2589 frente a 0.2694).")]
    story += [p("En el LSTM, ∂L/∂h<sub>k</sub> = (∂L/∂h<sub>T</sub>) Π<super>T</super><sub>t=k+1</sub> ∂h<sub>t</sub>/∂h<sub>t-1</sub> y ∂c<sub>t</sub>/∂c<sub>t-1</sub> = diag(f<sub>t</sub>). El gradiente hacia lags 48-80 atraviesa decenas de factores y puede decaer geométricamente.")]
    story += [p("En el Transformer, o<sub>0</sub> = Σ<sub>s</sub> α<sub>0s</sub>v<sub>s</sub>W<sub>O</sub>, de modo que existe un camino de longitud 1 desde cualquier posición atendida hasta la salida. Esto facilita aprender de lags lejanos como 45-48 y 70-74, precisamente donde se concentra el modelo H=48. La loss H=48 del LSTM queda aproximadamente entre 0.218 y 0.235, mientras la del Transformer baja de 0.1907 a 0.1794.")]

    # AI use
    story += [PageBreak(), p("Uso de IA generativa", H1)]
    story += [p("Se documenta, por cada task, el prompt exacto utilizado y la razón por la que resultó útil, conforme a las instrucciones del laboratorio.")]
    for task in range(1, 5):
        item = prompts[str(task)]
        story += [p(f"Task {task}", H2)]
        story += [p("Prompt exacto", H3), p(esc(item["prompt"]), PROMPT)]
        story += [p("Por qué funcionó", H3), p(esc(item["why"]))]

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.62 * inch,
        leftMargin=0.62 * inch,
        topMargin=0.66 * inch,
        bottomMargin=0.58 * inch,
        title="Laboratorio 7 - Respuestas",
        author="Diego López #23747",
        subject="Deep Learning (CC3092), Sección 20",
    )
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    print(OUT)


if __name__ == "__main__":
    build()
