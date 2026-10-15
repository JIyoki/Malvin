#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Malvin: Maquetado automatico   -   v1.4
----------------------------------------
PDF (una cuartilla por pagina) -> PDF listo para imprimir.

Estilos de maquetado
  sencillo   Sencillo (1/2)            cuadernillo, 2 paginas por lado
  bolsillo   Libro de bolsillo (1/4)   2x2 por lado, se corta en 2 cuadernillos
  multi      Multicuadernillo          cuadernillos de 1 hoja (4 paginas) seguidos
  dup2       Duplicado sin maquetado   cada pagina 2 veces en la hoja
  dup4       Cuadruplicado de bolsillo cada pagina 4 veces en la hoja
  sin        Sin maquetado             solo rasterizado (ideal para numerar)

Lomo: izquierda (defecto), superior o derecha (p.ej. japones).
Extras: numeracion, recorte de margen interior/exterior, marcas de doblez,
corte y borde de la pagina original, 4 idiomas (es / en / pt / ru).

Dependencias:  pip install pypdfium2 pillow
Uso:
  python malvin.py                 (abre la ventana)
  python malvin.py libro.pdf       (abre la ventana con el PDF cargado)
  python malvin.py libro.pdf -m bolsillo --lomo derecha --num --lang en   (consola)
"""
import argparse
import io
import os
import sys
import threading

__version__ = "1.4"
ICON_NAME = "icomalvin.ico"

try:  # consolas de Windows: evita errores con acentos / cirilico
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Missing dependencies / Faltan dependencias:  pip install pypdfium2 pillow")

# ------------------------------------------------------------------ idiomas
LANGS = {"es": "Español", "en": "English", "pt": "Português", "ru": "Русский"}
LANG = "en"

TR = {
"es": {
 "title": "Malvin: Maquetado automático",
 "tab_main": "Maquetado", "tab_marks": "Márgenes y marcas", "tab_num": "Numeración",
 "grp_files": "Archivos", "lbl_pdf": "PDF original:", "btn_browse": "Buscar...",
 "lbl_save": "Guardar en:", "btn_change": "Cambiar...",
 "info_pick": "Elige un PDF.",
 "info_pages": "{n} páginas -> {h} hojas ({c} caras)",
 "info_pages1": "{n} páginas -> {n} hojas",
 "err_read": "No pude leer el PDF: {e}",
 "grp_layout": "Estilo de maquetado",
 "mode_sencillo": "Sencillo (1/2)",
 "mode_sencillo_d": "2 páginas por lado; se dobla por la mitad y se engrapa",
 "mode_bolsillo": "Libro de bolsillo (1/4)",
 "mode_bolsillo_d": "2x2 por lado; se corta en 2 cuadernillos",
 "mode_dup2": "Duplicado sin maquetado",
 "mode_dup2_d": "cada página 2 veces en la hoja, sin reordenar",
 "mode_dup4": "Cuadruplicado de bolsillo sin maquetado",
 "mode_dup4_d": "cada página 4 veces en la hoja, sin reordenar",
 "mode_sin": "Sin maquetado",
 "mode_sin_d": "cada página tal cual, solo rasterizada (ideal para numerar)",
 "lbl_sheet": "Hoja:", "lbl_dpi": "DPI:", "lbl_spine": "Lomo del libro:",
 "lbl_inset": "Margen alrededor de cada página (mm):",
 "chk_backcover": "La última página es la contraportada (los blancos de relleno van antes de ella)",
 "chk_gray": "Escala de grises (archivo más ligero)",
 "lbl_crop_in": "Recortar margen interior (mm):", "lbl_crop_out": "Recortar margen exterior (mm):",
 "hint_crop": "Recorta esa cantidad del borde de cada página (del lado del lomo o del lado exterior) y desplaza el contenido hacia ese borde. Sirve cuando los márgenes del documento son simétricos y, al juntarse en el lomo, el margen interior se ve más grande que el exterior (o al revés).",
 "lbl_fold": "Marca de doblez (centro):", "lbl_fold_where": "En las hojas:",
 "lbl_cut": "Corte (estilos con varias copias por hoja):",
 "lbl_border": "Marcar el borde de cada página original:",
 "hint_marks": "Se dibujan sobre la hoja ya maquetada. «Marcas» = rayitas en el borde de la hoja; «Línea» = línea punteada completa (puede cruzar el contenido; usa el margen alrededor de cada página para dejarle espacio). El borde de la página (esquinas o contorno) ayuda a recortar cuando el formato original no es una mitad exacta de la hoja, como el tamaño cuarta.",
 "chk_num": "Numerar páginas", "lbl_from": "Empezar en la página (del PDF):",
 "lbl_call": "y llamarla número:", "lbl_to": "Hasta la página (0 = final):",
 "lbl_fmt": "Formato ({n} = número):", "lbl_font": "Fuente:", "btn_ttf": "Archivo .ttf...",
 "lbl_size": "Tamaño (pt):", "chk_bold": "Negrita",
 "lbl_vert": "Posición vertical:", "lbl_horiz": "Horizontal:",
 "lbl_mv": "Distancia al borde superior/inferior (mm):",
 "lbl_mh": "Distancia al borde lateral (mm):",
 "hint_num": "Izquierda/derecha/exterior/interior se miden en la página ya doblada (las páginas impares son las de la derecha si el lomo está a la izquierda). La distancia lateral no se usa en «centro». Con lomo superior, exterior/interior se tratan como centro.",
 "grp_order": "Vista previa del orden de impresión", "btn_run": "Maquetar",
 "opt_inferior": "inferior", "opt_superior": "superior", "opt_izquierda": "izquierda",
 "opt_centro": "centro", "opt_derecha": "derecha", "opt_exterior": "exterior",
 "opt_interior": "interior", "opt_ninguna": "ninguna", "opt_marcas": "marcas",
 "opt_linea": "línea", "opt_esquinas": "esquinas", "opt_contorno": "contorno",
 "opt_extremos": "primera y última", "opt_todas": "todas",
 "sheet_carta": "carta", "sheet_oficio": "oficio", "sheet_legal": "legal",
 "sheet_a4": "A4", "sheet_a3": "A3", "sheet_tabloide": "tabloide",
 "msg_pick_pdf": "Elige un PDF válido.", "msg_numbers": "Revisa los números de las opciones.",
 "msg_done": "Listo:\n{dst}\n\nImprime a tamaño real (100%, sin ajustar a la página).\n{tip}",
 "tip_short": "Imprime a doble cara, volteando por el BORDE CORTO. Dobla por la mitad y engrapa en el lomo.",
 "tip_long": "Imprime a doble cara, volteando por el BORDE LARGO. Corta la hoja por la mitad, dobla y engrapa: salen 2 cuadernillos.",
 "tip_dup2": "Imprime a una sola cara. Corta cada hoja por la mitad, apila las mitades en orden y engrapa por el lado del lomo.",
 "tip_dup4": "Imprime a una sola cara. Corta cada hoja en cuatro, apila los cuartos en orden y engrapa por el lado del lomo.",
 "tip_sin": "Cada página conserva su tamaño original.",
 "err_prefix": "Error: {e}", "err_nopages": "El PDF no tiene páginas.",
 "log_pages": "Páginas originales: {t}  ->  con relleno: {n}  ({h} hojas, {c} caras)",
 "log_pages1": "Páginas originales: {t}  ->  {t} hojas",
 "log_cfg": "Hoja {s} | estilo: {m} | lomo: {sp} | {d} dpi",
 "plan_line": "  Hoja {k}:  frente {f}   |   reverso {b}", "blank": "blanco",
 "plan_dup2": "  Hoja {k}:  {p} y {p}",
 "plan_dup4": "  Hoja {k}:  {p}, {p}, {p} y {p}",
 "plan_sin": "  Hoja {k}:  {p}",
 "log_num": "Numeración: páginas {a} a {b} del original, empieza en {i}, {t} pt, {font}{bold}, {v}-{h}",
 "bold_word": " negrita",
 "warn_font": "Aviso: no encontré la fuente '{f}'; se usó una de respaldo. Escribe la ruta completa a un .ttf.",
 "log_scale": "Escala aplicada a la peor página: {p}% del tamaño original",
 "log_slot": "Hueco por página: {w:.2f} x {h:.2f} in ({wm:.0f} x {hm:.0f} mm)",
 "log_print": "IMPRESIÓN: tamaño real (100%, sin ajustar a la página).",
 "log_done": "Listo: {dst}",
},
"en": {
 "title": "Malvin: Automatic imposition",
 "tab_main": "Layout", "tab_marks": "Margins & marks", "tab_num": "Page numbers",
 "grp_files": "Files", "lbl_pdf": "Source PDF:", "btn_browse": "Browse...",
 "lbl_save": "Save as:", "btn_change": "Change...",
 "info_pick": "Choose a PDF.",
 "info_pages": "{n} pages -> {h} sheets ({c} sides)",
 "info_pages1": "{n} pages -> {n} sheets",
 "err_read": "Could not read the PDF: {e}",
 "grp_layout": "Layout style",
 "mode_sencillo": "Single booklet (1/2)",
 "mode_sencillo_d": "2 pages per side; fold in half and staple",
 "mode_bolsillo": "Pocket book (1/4)",
 "mode_bolsillo_d": "2x2 per side; cut into 2 booklets",
 "mode_dup2": "Duplicate, no imposition",
 "mode_dup2_d": "each page twice on the sheet, order unchanged",
 "mode_dup4": "Pocket quadruplicate, no imposition",
 "mode_dup4_d": "each page four times on the sheet, order unchanged",
 "mode_sin": "No imposition",
 "mode_sin_d": "each page as is, only rasterized (ideal for numbering)",
 "lbl_sheet": "Sheet:", "lbl_dpi": "DPI:", "lbl_spine": "Book spine:",
 "lbl_inset": "Margin around each page (mm):",
 "chk_backcover": "Last page is the back cover (filler blanks go before it)",
 "chk_gray": "Grayscale (smaller file)",
 "lbl_crop_in": "Trim inner margin (mm):", "lbl_crop_out": "Trim outer margin (mm):",
 "hint_crop": "Cuts that amount off the edge of each page (spine side or outer side) and slides the content toward that edge. Useful when the document's margins are symmetric and, once joined at the spine, the inner margin looks bigger than the outer one (or vice versa).",
 "lbl_fold": "Fold mark (center):", "lbl_fold_where": "On sheets:",
 "lbl_cut": "Cut (styles with several copies per sheet):",
 "lbl_border": "Mark the edge of each original page:",
 "hint_marks": "Drawn on the finished sheet. 'Marks' = small ticks on the sheet edge; 'Line' = full dashed line (may cross content; use the margin around each page to leave room). The page edge (corners or outline) helps when trimming if the original format is not an exact half of the sheet, such as quarter-size documents.",
 "chk_num": "Number pages", "lbl_from": "Start at page (of the PDF):",
 "lbl_call": "and call it number:", "lbl_to": "Up to page (0 = end):",
 "lbl_fmt": "Format ({n} = number):", "lbl_font": "Font:", "btn_ttf": ".ttf file...",
 "lbl_size": "Size (pt):", "chk_bold": "Bold",
 "lbl_vert": "Vertical position:", "lbl_horiz": "Horizontal:",
 "lbl_mv": "Distance to top/bottom edge (mm):",
 "lbl_mh": "Distance to side edge (mm):",
 "hint_num": "Left/right/outer/inner are measured on the folded page (odd pages are the right-hand ones when the spine is on the left). Side distance is ignored for 'center'. With a top spine, outer/inner are treated as center.",
 "grp_order": "Print order preview", "btn_run": "Impose",
 "opt_inferior": "bottom", "opt_superior": "top", "opt_izquierda": "left",
 "opt_centro": "center", "opt_derecha": "right", "opt_exterior": "outer",
 "opt_interior": "inner", "opt_ninguna": "none", "opt_marcas": "marks",
 "opt_linea": "line", "opt_esquinas": "corners", "opt_contorno": "outline",
 "opt_extremos": "first and last", "opt_todas": "all",
 "sheet_carta": "Letter", "sheet_oficio": "Mexican legal (8.5x13)", "sheet_legal": "Legal",
 "sheet_a4": "A4", "sheet_a3": "A3", "sheet_tabloide": "Tabloid",
 "msg_pick_pdf": "Choose a valid PDF.", "msg_numbers": "Check the numbers in the options.",
 "msg_done": "Done:\n{dst}\n\nPrint at actual size (100%, do not fit to page).\n{tip}",
 "tip_short": "Print double-sided, flipping on the SHORT EDGE. Fold in half and staple on the spine.",
 "tip_long": "Print double-sided, flipping on the LONG EDGE. Cut the sheet in half, fold and staple: you get 2 booklets.",
 "tip_dup2": "Print single-sided. Cut each sheet in half, stack the halves in order and staple on the spine side.",
 "tip_dup4": "Print single-sided. Cut each sheet in four, stack the quarters in order and staple on the spine side.",
 "tip_sin": "Each page keeps its original size.",
 "err_prefix": "Error: {e}", "err_nopages": "The PDF has no pages.",
 "log_pages": "Source pages: {t}  ->  padded: {n}  ({h} sheets, {c} sides)",
 "log_pages1": "Source pages: {t}  ->  {t} sheets",
 "log_cfg": "Sheet {s} | style: {m} | spine: {sp} | {d} dpi",
 "plan_line": "  Sheet {k}:  front {f}   |   back {b}", "blank": "blank",
 "plan_dup2": "  Sheet {k}:  {p} and {p}",
 "plan_dup4": "  Sheet {k}:  {p}, {p}, {p} and {p}",
 "plan_sin": "  Sheet {k}:  {p}",
 "log_num": "Numbering: source pages {a} to {b}, starts at {i}, {t} pt, {font}{bold}, {v}-{h}",
 "bold_word": " bold",
 "warn_font": "Warning: font '{f}' not found; a fallback was used. Type the full path to a .ttf file.",
 "log_scale": "Scale applied to the worst page: {p}% of original size",
 "log_slot": "Slot per page: {w:.2f} x {h:.2f} in ({wm:.0f} x {hm:.0f} mm)",
 "log_print": "PRINTING: actual size (100%, do not fit to page).",
 "log_done": "Done: {dst}",
},
"pt": {
 "title": "Malvin: Diagramação automática",
 "tab_main": "Diagramação", "tab_marks": "Margens e marcas", "tab_num": "Numeração",
 "grp_files": "Arquivos", "lbl_pdf": "PDF original:", "btn_browse": "Procurar...",
 "lbl_save": "Salvar em:", "btn_change": "Alterar...",
 "info_pick": "Escolha um PDF.",
 "info_pages": "{n} páginas -> {h} folhas ({c} faces)",
 "info_pages1": "{n} páginas -> {n} folhas",
 "err_read": "Não consegui ler o PDF: {e}",
 "grp_layout": "Estilo de diagramação",
 "mode_sencillo": "Simples (1/2)",
 "mode_sencillo_d": "2 páginas por face; dobra-se ao meio e grampeia-se",
 "mode_bolsillo": "Livro de bolso (1/4)",
 "mode_bolsillo_d": "2x2 por face; corta-se em 2 cadernos",
 "mode_dup2": "Duplicado sem diagramação",
 "mode_dup2_d": "cada página 2 vezes na folha, sem reordenar",
 "mode_dup4": "Quadruplicado de bolso sem diagramação",
 "mode_dup4_d": "cada página 4 vezes na folha, sem reordenar",
 "mode_sin": "Sem diagramação",
 "mode_sin_d": "cada página como está, só rasterizada (ideal para numerar)",
 "lbl_sheet": "Folha:", "lbl_dpi": "DPI:", "lbl_spine": "Lombada do livro:",
 "lbl_inset": "Margem ao redor de cada página (mm):",
 "chk_backcover": "A última página é a contracapa (os brancos de preenchimento vão antes dela)",
 "chk_gray": "Tons de cinza (arquivo mais leve)",
 "lbl_crop_in": "Cortar margem interna (mm):", "lbl_crop_out": "Cortar margem externa (mm):",
 "hint_crop": "Corta essa quantidade da borda de cada página (do lado da lombada ou do lado externo) e desloca o conteúdo para essa borda. Útil quando as margens do documento são simétricas e, ao se juntarem na lombada, a margem interna parece maior que a externa (ou o contrário).",
 "lbl_fold": "Marca de dobra (centro):", "lbl_fold_where": "Nas folhas:",
 "lbl_cut": "Corte (estilos com várias cópias por folha):",
 "lbl_border": "Marcar a borda de cada página original:",
 "hint_marks": "Desenhadas sobre a folha já diagramada. «Marcas» = tracinhos na borda da folha; «Linha» = linha pontilhada completa (pode cruzar o conteúdo; use a margem ao redor de cada página para dar espaço). A borda da página (cantos ou contorno) ajuda a aparar quando o formato original não é exatamente metade da folha, como em tamanho quarto.",
 "chk_num": "Numerar páginas", "lbl_from": "Começar na página (do PDF):",
 "lbl_call": "e chamá-la de número:", "lbl_to": "Até a página (0 = fim):",
 "lbl_fmt": "Formato ({n} = número):", "lbl_font": "Fonte:", "btn_ttf": "Arquivo .ttf...",
 "lbl_size": "Tamanho (pt):", "chk_bold": "Negrito",
 "lbl_vert": "Posição vertical:", "lbl_horiz": "Horizontal:",
 "lbl_mv": "Distância da borda superior/inferior (mm):",
 "lbl_mh": "Distância da borda lateral (mm):",
 "hint_num": "Esquerda/direita/externa/interna são medidas na página já dobrada (as páginas ímpares ficam à direita quando a lombada está à esquerda). A distância lateral não é usada em «centro». Com lombada superior, externa/interna são tratadas como centro.",
 "grp_order": "Pré-visualização da ordem de impressão", "btn_run": "Diagramar",
 "opt_inferior": "inferior", "opt_superior": "superior", "opt_izquierda": "esquerda",
 "opt_centro": "centro", "opt_derecha": "direita", "opt_exterior": "externa",
 "opt_interior": "interna", "opt_ninguna": "nenhuma", "opt_marcas": "marcas",
 "opt_linea": "linha", "opt_esquinas": "cantos", "opt_contorno": "contorno",
 "opt_extremos": "primeira e última", "opt_todas": "todas",
 "sheet_carta": "Carta", "sheet_oficio": "Ofício (8,5x13)", "sheet_legal": "Legal",
 "sheet_a4": "A4", "sheet_a3": "A3", "sheet_tabloide": "Tabloide",
 "msg_pick_pdf": "Escolha um PDF válido.", "msg_numbers": "Verifique os números das opções.",
 "msg_done": "Pronto:\n{dst}\n\nImprima em tamanho real (100%, sem ajustar à página).\n{tip}",
 "tip_short": "Imprima frente e verso, virando pela BORDA CURTA. Dobre ao meio e grampeie na lombada.",
 "tip_long": "Imprima frente e verso, virando pela BORDA LONGA. Corte a folha ao meio, dobre e grampeie: saem 2 cadernos.",
 "tip_dup2": "Imprima só de um lado. Corte cada folha ao meio, empilhe as metades em ordem e grampeie do lado da lombada.",
 "tip_dup4": "Imprima só de um lado. Corte cada folha em quatro, empilhe os quartos em ordem e grampeie do lado da lombada.",
 "tip_sin": "Cada página mantém seu tamanho original.",
 "err_prefix": "Erro: {e}", "err_nopages": "O PDF não tem páginas.",
 "log_pages": "Páginas originais: {t}  ->  com preenchimento: {n}  ({h} folhas, {c} faces)",
 "log_pages1": "Páginas originais: {t}  ->  {t} folhas",
 "log_cfg": "Folha {s} | estilo: {m} | lombada: {sp} | {d} dpi",
 "plan_line": "  Folha {k}:  frente {f}   |   verso {b}", "blank": "branco",
 "plan_dup2": "  Folha {k}:  {p} e {p}",
 "plan_dup4": "  Folha {k}:  {p}, {p}, {p} e {p}",
 "plan_sin": "  Folha {k}:  {p}",
 "log_num": "Numeração: páginas {a} a {b} do original, começa em {i}, {t} pt, {font}{bold}, {v}-{h}",
 "bold_word": " negrito",
 "warn_font": "Aviso: não encontrei a fonte '{f}'; foi usada uma reserva. Digite o caminho completo de um .ttf.",
 "log_scale": "Escala aplicada à pior página: {p}% do tamanho original",
 "log_slot": "Espaço por página: {w:.2f} x {h:.2f} in ({wm:.0f} x {hm:.0f} mm)",
 "log_print": "IMPRESSÃO: tamanho real (100%, sem ajustar à página).",
 "log_done": "Pronto: {dst}",
},
"ru": {
 "title": "Malvin: Автоматическая верстка",
 "tab_main": "Верстка", "tab_marks": "Поля и метки", "tab_num": "Нумерация",
 "grp_files": "Файлы", "lbl_pdf": "Исходный PDF:", "btn_browse": "Обзор...",
 "lbl_save": "Сохранить в:", "btn_change": "Изменить...",
 "info_pick": "Выберите PDF.",
 "info_pages": "{n} стр. -> {h} листов ({c} сторон)",
 "info_pages1": "{n} стр. -> {n} листов",
 "err_read": "Не удалось прочитать PDF: {e}",
 "grp_layout": "Стиль верстки",
 "mode_sencillo": "Одинарный (1/2)",
 "mode_sencillo_d": "2 страницы на стороне; сложить пополам и скрепить",
 "mode_bolsillo": "Карманная книга (1/4)",
 "mode_bolsillo_d": "2x2 на стороне; разрезать на 2 буклета",
 "mode_dup2": "Дублирование без верстки",
 "mode_dup2_d": "каждая страница 2 раза на листе, порядок прежний",
 "mode_dup4": "Карманное четырёхкратное без верстки",
 "mode_dup4_d": "каждая страница 4 раза на листе, порядок прежний",
 "mode_sin": "Без верстки",
 "mode_sin_d": "каждая страница как есть, только растеризация (удобно для нумерации)",
 "lbl_sheet": "Лист:", "lbl_dpi": "DPI:", "lbl_spine": "Корешок книги:",
 "lbl_inset": "Отступ вокруг каждой страницы (мм):",
 "chk_backcover": "Последняя страница — задняя обложка (пустые страницы ставятся перед ней)",
 "chk_gray": "Оттенки серого (файл меньше)",
 "lbl_crop_in": "Обрезать внутреннее поле (мм):", "lbl_crop_out": "Обрезать внешнее поле (мм):",
 "hint_crop": "Отрезает указанную величину от края каждой страницы (со стороны корешка или внешней) и сдвигает содержимое к этому краю. Полезно, когда поля документа симметричны и после соединения у корешка внутреннее поле выглядит больше внешнего (или наоборот).",
 "lbl_fold": "Метка сгиба (центр):", "lbl_fold_where": "На листах:",
 "lbl_cut": "Рез (стили с несколькими копиями на листе):",
 "lbl_border": "Отметить край каждой исходной страницы:",
 "hint_marks": "Рисуются на уже сверстанном листе. «Метки» = короткие штрихи на краю листа; «Линия» = сплошная пунктирная линия (может пересекать содержимое; оставьте место отступом вокруг страницы). Край страницы (углы или контур) помогает при обрезке, если исходный формат не ровно половина листа, например формат в четверть листа.",
 "chk_num": "Нумеровать страницы", "lbl_from": "Начать со страницы (PDF):",
 "lbl_call": "и назвать её номером:", "lbl_to": "До страницы (0 = конец):",
 "lbl_fmt": "Формат ({n} = номер):", "lbl_font": "Шрифт:", "btn_ttf": "Файл .ttf...",
 "lbl_size": "Размер (пт):", "chk_bold": "Жирный",
 "lbl_vert": "Положение по вертикали:", "lbl_horiz": "По горизонтали:",
 "lbl_mv": "Расстояние до верхнего/нижнего края (мм):",
 "lbl_mh": "Расстояние до бокового края (мм):",
 "hint_num": "Слева/справа/снаружи/внутри считается на сложенной странице (нечётные страницы справа, если корешок слева). Боковое расстояние не используется для «центр». При верхнем корешке «снаружи/внутри» считаются как «центр».",
 "grp_order": "Предпросмотр порядка печати", "btn_run": "Сверстать",
 "opt_inferior": "снизу", "opt_superior": "сверху", "opt_izquierda": "слева",
 "opt_centro": "центр", "opt_derecha": "справа", "opt_exterior": "снаружи",
 "opt_interior": "внутри", "opt_ninguna": "нет", "opt_marcas": "метки",
 "opt_linea": "линия", "opt_esquinas": "углы", "opt_contorno": "контур",
 "opt_extremos": "первый и последний", "opt_todas": "все",
 "sheet_carta": "Letter", "sheet_oficio": "Oficio (8,5x13)", "sheet_legal": "Legal",
 "sheet_a4": "A4", "sheet_a3": "A3", "sheet_tabloide": "Tabloid",
 "msg_pick_pdf": "Выберите корректный PDF.", "msg_numbers": "Проверьте числа в настройках.",
 "msg_done": "Готово:\n{dst}\n\nПечатайте в реальном размере (100%, без подгонки под страницу).\n{tip}",
 "tip_short": "Печать с двух сторон, переворот по КОРОТКОМУ краю. Сложите пополам и скрепите по корешку.",
 "tip_long": "Печать с двух сторон, переворот по ДЛИННОМУ краю. Разрежьте лист пополам, сложите и скрепите: получится 2 буклета.",
 "tip_dup2": "Печать с одной стороны. Разрежьте каждый лист пополам, сложите половинки по порядку и скрепите со стороны корешка.",
 "tip_dup4": "Печать с одной стороны. Разрежьте каждый лист на четыре части, сложите по порядку и скрепите со стороны корешка.",
 "tip_sin": "Каждая страница сохраняет исходный размер.",
 "err_prefix": "Ошибка: {e}", "err_nopages": "В PDF нет страниц.",
 "log_pages": "Исходных страниц: {t}  ->  с добавлением пустых: {n}  ({h} листов, {c} сторон)",
 "log_pages1": "Исходных страниц: {t}  ->  {t} листов",
 "log_cfg": "Лист {s} | стиль: {m} | корешок: {sp} | {d} dpi",
 "plan_line": "  Лист {k}:  лицо {f}   |   оборот {b}", "blank": "пусто",
 "plan_dup2": "  Лист {k}:  {p} и {p}",
 "plan_dup4": "  Лист {k}:  {p}, {p}, {p} и {p}",
 "plan_sin": "  Лист {k}:  {p}",
 "log_num": "Нумерация: страницы {a}–{b} исходника, начало с {i}, {t} пт, {font}{bold}, {v}-{h}",
 "bold_word": " жирный",
 "warn_font": "Внимание: шрифт '{f}' не найден, использован запасной. Укажите полный путь к файлу .ttf.",
 "log_scale": "Масштаб для худшей страницы: {p}% от исходного размера",
 "log_slot": "Место под страницу: {w:.2f} x {h:.2f} дюйм ({wm:.0f} x {hm:.0f} мм)",
 "log_print": "ПЕЧАТЬ: реальный размер (100%, без подгонки под страницу).",
 "log_done": "Готово: {dst}",
},
}


TR["es"].update({
 "btn_preview": "Vista previa del diseño",
 "prev_title": "Vista previa del diseño de impresión",
 "prev_sheet": "Hoja {k}", "prev_front": "frente", "prev_back": "reverso",
 "prev_zoom": "Zoom:", "prev_loading": "Generando vista previa...",
 "prev_limit": "Mostrando las primeras {m} de {n} hojas.",
 "prev_hint": "Cada hoja se muestra como saldrá impresa, con las opciones actuales.",
})
TR["en"].update({
 "btn_preview": "Layout preview",
 "prev_title": "Print layout preview",
 "prev_sheet": "Sheet {k}", "prev_front": "front", "prev_back": "back",
 "prev_zoom": "Zoom:", "prev_loading": "Generating preview...",
 "prev_limit": "Showing the first {m} of {n} sheets.",
 "prev_hint": "Each sheet is shown as it will print, with the current options.",
})
TR["pt"].update({
 "btn_preview": "Pré-visualizar diagramação",
 "prev_title": "Pré-visualização do layout de impressão",
 "prev_sheet": "Folha {k}", "prev_front": "frente", "prev_back": "verso",
 "prev_zoom": "Zoom:", "prev_loading": "Gerando pré-visualização...",
 "prev_limit": "Mostrando as primeiras {m} de {n} folhas.",
 "prev_hint": "Cada folha é mostrada como será impressa, com as opções atuais.",
})
TR["ru"].update({
 "btn_preview": "Предпросмотр верстки",
 "prev_title": "Предпросмотр макета печати",
 "prev_sheet": "Лист {k}", "prev_front": "лицо", "prev_back": "оборот",
 "prev_zoom": "Масштаб:", "prev_loading": "Создание предпросмотра...",
 "prev_limit": "Показаны первые {m} из {n} листов.",
 "prev_hint": "Каждый лист показан так, как он будет напечатан, с текущими настройками.",
})

TR["es"].update({
 "mode_multi": "Multicuadernillo",
 "mode_multi_d": "cuadernillos de 1 hoja (4 páginas) seguidos, para unir por el lomo",
 "tip_multi": "Imprime a doble cara, volteando por el BORDE CORTO. Dobla cada hoja por la mitad (conviene doblar de 5 en 5 hojas para no maltratar el papel), apila los cuadernillos en orden y únelos por el lomo.",
})
TR["en"].update({
 "mode_multi": "Multi-signature",
 "mode_multi_d": "consecutive 1-sheet (4-page) signatures, to join at the spine",
 "tip_multi": "Print double-sided, flipping on the SHORT EDGE. Fold each sheet in half (folding 5 at a time is easier on the paper), stack the signatures in order and join them at the spine.",
})
TR["pt"].update({
 "mode_multi": "Multicadernos",
 "mode_multi_d": "cadernos de 1 folha (4 páginas) em sequência, para unir na lombada",
 "tip_multi": "Imprima frente e verso, virando pela BORDA CURTA. Dobre cada folha ao meio (convém dobrar de 5 em 5 folhas para não maltratar o papel), empilhe os cadernos em ordem e una-os na lombada.",
})
TR["ru"].update({
 "mode_multi": "Набор тетрадей",
 "mode_multi_d": "последовательные тетради по 1 листу (4 страницы), для склейки по корешку",
 "tip_multi": "Печать с двух сторон, переворот по КОРОТКОМУ краю. Сложите каждый лист пополам (удобнее складывать по 5 листов сразу, чтобы не мять бумагу), сложите тетради по порядку и соедините по корешку.",
})

TR["es"].update({
 "grp_preview": "Vista previa", "view_print": "Diseño de impresión", "view_result": "Resultado esperado",
 "theme_auto": "Automático", "theme_light": "Claro", "theme_dark": "Oscuro",
 "prev_limit2": "Mostrando las primeras {m} de {n} vistas.",
})
TR["en"].update({
 "grp_preview": "Preview", "view_print": "Print layout", "view_result": "Expected result",
 "theme_auto": "Auto", "theme_light": "Light", "theme_dark": "Dark",
 "prev_limit2": "Showing the first {m} of {n} views.",
})
TR["pt"].update({
 "grp_preview": "Pré-visualização", "view_print": "Layout de impressão", "view_result": "Resultado esperado",
 "theme_auto": "Automático", "theme_light": "Claro", "theme_dark": "Escuro",
 "prev_limit2": "Mostrando as primeiras {m} de {n} vistas.",
})
TR["ru"].update({
 "grp_preview": "Предпросмотр", "view_print": "Макет печати", "view_result": "Ожидаемый результат",
 "theme_auto": "Авто", "theme_light": "Светлая", "theme_dark": "Тёмная",
 "prev_limit2": "Показаны первые {m} из {n} видов.",
})

# ---- idiomas extra: archivos idiomas/<codigo>.lang  (clave=valor, UTF-8) ----
RTL_LANGS = {"ar", "fa"}


def _res_dir(name):
    here = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    for d in (here, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.isdir(p):
            return p
    return None


def load_extra_langs():
    """Carga idiomas/*.lang. Linea: clave=valor ; '#' comenta ; \\n = salto de linea.
    '_name' es el nombre del idioma en su propio idioma. Lo que falte cae a ingles."""
    d = _res_dir("idiomas")
    if not d:
        return
    for fn in sorted(os.listdir(d)):
        code = fn[:-5].lower()
        if not fn.lower().endswith(".lang") or code in TR:
            continue
        data = {}
        try:
            with open(os.path.join(d, fn), encoding="utf-8-sig") as f:
                for line in f:
                    line = line.rstrip("\r\n")
                    if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.replace("\\n", "\n")
        except OSError:
            continue
        name = data.pop("_name", code)
        if data:
            TR[code], LANGS[code] = data, name


load_extra_langs()


def shape(s, rtl=None):
    """Arabe/persa: une letras y reordena (solo si estan instalados
    arabic-reshaper y python-bidi; si no, devuelve el texto tal cual)."""
    if rtl is None:
        rtl = LANG in RTL_LANGS
    if not rtl:
        return s
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(s))
    except Exception:
        return s


def T(key, **kw):
    s = TR.get(LANG, TR["en"]).get(key) or TR["en"][key]
    return s.format(**kw) if kw else s


def set_lang(code):
    global LANG
    LANG = code if code in TR else "en"


def detect_lang():
    """Idioma del sistema; si no esta entre los disponibles -> ingles."""
    win = {0x0A: "es", 0x09: "en", 0x16: "pt", 0x19: "ru", 0x1E: "th", 0x21: "id",
           0x3E: "id", 0x64: "fil", 0x39: "hi", 0x01: "ar", 0x11: "ja", 0x1F: "tr",
           0x04: "zh", 0x07: "de", 0x0C: "fr", 0x22: "uk", 0x18: "ro", 0x1A: "sh",
           0x29: "fa", 0x10: "it", 0x08: "el", 0x12: "ko"}
    code = None
    try:  # Windows: idioma de la interfaz
        import ctypes
        code = win.get(ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF)
    except Exception:
        raw = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES")
               or os.environ.get("LANG") or "").lower()
        alt = {"ms": "id", "hr": "sh", "sr": "sh", "bs": "sh", "tl": "fil", "fil": "fil"}
        for cand in (raw[:3], raw[:2]):
            if cand in TR:
                code = cand
                break
            if cand in alt:
                code = alt[cand]
                break
    return code if code in TR else "en"


# ---------------------------------------------------------------- constantes
MODES = ["sencillo", "bolsillo", "multi", "dup2", "dup4", "sin"]
IMPOSED = ("sencillo", "bolsillo", "multi")
SPINES = ["izquierda", "superior", "derecha"]
SHEET_KEYS = ["carta", "oficio", "legal", "a4", "a3", "tabloide"]
SHEETS = {  # (ancho, alto) en pulgadas, vertical
    "carta": (8.5, 11.0), "oficio": (8.5, 13.0), "legal": (8.5, 14.0),
    "a4": (8.27, 11.69), "a3": (11.69, 16.54), "tabloide": (11.0, 17.0),
}
SHEETS["letter"] = SHEETS["carta"]      # alias para la consola
SHEETS["tabloid"] = SHEETS["tabloide"]

VERT_OPTS = ["inferior", "superior"]
HORIZ_OPTS = ["izquierda", "centro", "derecha", "exterior", "interior"]
STYLE_OPTS = ["ninguna", "marcas", "linea"]
BORDER_OPTS = ["ninguna", "esquinas", "contorno"]
WHERE_OPTS = ["extremos", "todas"]
ALIASES = {"bottom": "inferior", "top": "superior", "left": "izquierda",
           "center": "centro", "centre": "centro", "right": "derecha",
           "outer": "exterior", "outside": "exterior", "inner": "interior",
           "inside": "interior", "none": "ninguna", "marks": "marcas",
           "line": "linea", "ends": "extremos", "first-last": "extremos",
           "all": "todas", "corners": "esquinas", "outline": "contorno"}
MODE_ALIASES = {"2": "sencillo", "1/2": "sencillo", "booklet": "sencillo", "single": "sencillo",
                "4": "bolsillo", "1/4": "bolsillo", "pocket": "bolsillo",
                "multicuadernillo": "multi", "signatures": "multi", "multisig": "multi",
                "dup": "dup2", "duplicate": "dup2", "quad": "dup4", "quadruple": "dup4",
                "raw": "sin", "plain": "sin"}


def alias(v):
    return ALIASES.get(str(v).lower(), str(v).lower())


def alias_mode(v):
    return MODE_ALIASES.get(str(v).lower(), str(v).lower())


NUM_DEFAULT = {
    "activar": False,
    "desde": 1,         # pagina del PDF original donde empieza a numerar
    "inicio": 1,        # numero que lleva esa primera pagina numerada
    "hasta": 0,         # ultima pagina a numerar (0 = hasta el final)
    "tam": 12.0,        # puntos
    "fuente": "Arial",  # nombre de fuente instalada o ruta a un .ttf
    "negrita": False,
    "vert": "inferior",
    "horiz": "centro",
    "margen_v": 10.0,   # mm al borde superior/inferior de la pagina
    "margen_h": 15.0,   # mm al borde lateral de la pagina
    "formato": "{n}",
}
MARKS_DEFAULT = {
    "pliegue": "ninguna",         # ninguna | marcas | linea (centro, para doblar)
    "pliegue_hojas": "extremos",  # extremos (primera y ultima hoja) | todas
    "corte": "marcas",            # ninguna | marcas | linea (estilos con varias copias)
    "borde": "ninguna",           # ninguna | esquinas | contorno (borde de cada pagina)
}

FONT_FILES = {  # nombre amigable -> (normal, negrita)
    "arial": ("arial.ttf", "arialbd.ttf"),
    "times new roman": ("times.ttf", "timesbd.ttf"),
    "calibri": ("calibri.ttf", "calibrib.ttf"),
    "cambria": ("cambria.ttc", "cambriab.ttf"),
    "georgia": ("georgia.ttf", "georgiab.ttf"),
    "verdana": ("verdana.ttf", "verdanab.ttf"),
    "tahoma": ("tahoma.ttf", "tahomabd.ttf"),
    "courier new": ("cour.ttf", "courbd.ttf"),
    "consolas": ("consola.ttf", "consolab.ttf"),
    "segoe ui": ("segoeui.ttf", "segoeuib.ttf"),
    "comic sans ms": ("comic.ttf", "comicbd.ttf"),
    "garamond": ("GARA.TTF", "GARABD.TTF"),
    "dejavu sans": ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
    "dejavu serif": ("DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf"),
    "liberation sans": ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"),
    "liberation serif": ("LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf"),
    "liberation mono": ("LiberationMono-Regular.ttf", "LiberationMono-Bold.ttf"),
}
FONT_NAMES = [n.title() if n != "segoe ui" else "Segoe UI" for n in FONT_FILES]


# ----------------------------------------------------------- escritor de PDF
class MiniPDF:
    """Escribe un PDF pagina por pagina con JPEG incrustado (poca memoria,
    sin recomprimir)."""

    def __init__(self, path):
        self.f = open(path, "wb")
        self.f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        self.offs, self.kids, self.nid = {}, [], 3

    def _new(self):
        i = self.nid
        self.nid += 1
        return i

    def _put(self, oid, body):
        self.offs[oid] = self.f.tell()
        self.f.write(b"%d 0 obj\n" % oid + body + b"\nendobj\n")

    def add_page(self, jpeg, wpx, hpx, gray, dpi):
        wpt, hpt = wpx * 72.0 / dpi, hpx * 72.0 / dpi
        img_id, cont_id, page_id = self._new(), self._new(), self._new()
        cs = b"/DeviceGray" if gray else b"/DeviceRGB"
        self._put(img_id, b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                  b"/ColorSpace %s /BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n"
                  % (wpx, hpx, cs, len(jpeg)) + jpeg + b"\nendstream")
        content = b"q %.4f 0 0 %.4f 0 0 cm /Im0 Do Q" % (wpt, hpt)
        self._put(cont_id, b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        self._put(page_id, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.4f %.4f] "
                  b"/Resources << /XObject << /Im0 %d 0 R >> >> /Contents %d 0 R >>"
                  % (wpt, hpt, img_id, cont_id))
        self.kids.append(page_id)

    def close(self):
        kids = b" ".join(b"%d 0 R" % k for k in self.kids)
        self._put(2, b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % len(self.kids))
        self._put(1, b"<< /Type /Catalog /Pages 2 0 R >>")
        xref = self.f.tell()
        out = [b"xref\n0 %d\n" % self.nid, b"0000000000 65535 f \n"]
        out += [b"%010d 00000 n \n" % self.offs[i] for i in range(1, self.nid)]
        out.append(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (self.nid, xref))
        self.f.write(b"".join(out))
        self.f.close()


def jpeg_bytes(img, quality, dpi):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, dpi=(dpi, dpi))
    return buf.getvalue()


# ---------------------------------------------------------------- numeracion
def load_font(name, px, bold):
    """Devuelve (fuente, negrita_sintetica, es_la_pedida)."""
    name = (name or "").strip()
    cands = []  # (candidato, es_cara_negrita, es_la_pedida)
    if name and os.path.isfile(name):
        cands.append((name, False, True))
    else:
        key = name.lower()
        if key in FONT_FILES:
            reg, bd = FONT_FILES[key]
            if bold:
                cands.append((bd, True, True))
            cands.append((reg, False, True))
        elif name:
            cands += [(name, False, True), (name + ".ttf", False, True),
                      (name.lower() + ".ttf", False, True)]
    cands += [("DejaVuSans-Bold.ttf", True, False), ("DejaVuSans.ttf", False, False),
              ("arialbd.ttf", True, False), ("arial.ttf", False, False)]
    for c, is_bold_face, exact in cands:
        try:
            return ImageFont.truetype(c, px), (bold and not is_bold_face), exact
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=px), bold, False
    except TypeError:
        return ImageFont.load_default(), False, False


def page_on_right(src_idx, spine):
    """True si la pagina cae en el lado derecho del libro abierto."""
    odd = src_idx % 2 == 1
    return odd if spine == "izquierda" else (not odd)


def page_edges(src_idx, spine):
    """(borde_interior, borde_exterior) de la pagina: 'l','r','t','b'."""
    if spine == "superior":
        return "t", "b"
    return ("l", "r") if page_on_right(src_idx, spine) else ("r", "l")


def resolve_h(h, src_idx, spine):
    """Devuelve 'l', 'm' o 'r'."""
    if h in ("exterior", "interior"):
        if spine == "superior":
            return "m"
        right = page_on_right(src_idx, spine)
        if h == "interior":
            right = not right
        return "r" if right else "l"
    return {"izquierda": "l", "centro": "m", "derecha": "r"}.get(h, "m")


def draw_number(img, src_idx, num, dpi, font_cache, spine):
    """Dibuja el numero sobre la imagen de la pagina (src_idx 1-based)."""
    n = num["inicio"] + (src_idx - num["desde"])
    text = num["formato"].replace("{n}", str(n))
    px = max(1, round(num["tam"] / 72 * dpi))
    key = (num["fuente"], px, num["negrita"])
    if key not in font_cache:
        font_cache[key] = load_font(num["fuente"], px, num["negrita"])
    font, synth, _ = font_cache[key]
    mv = round(num["margen_v"] / 25.4 * dpi)
    mh = round(num["margen_h"] / 25.4 * dpi)
    h = resolve_h(num["horiz"], src_idx, spine)
    x = {"l": mh, "m": img.width // 2, "r": img.width - mh}[h]
    if num["vert"] == "superior":
        y, anchor = mv, h + "a"
    else:
        y, anchor = img.height - mv, h + "d"
    sw = max(1, px // 28) if synth else 0
    ImageDraw.Draw(img).text((x, y), text, font=font, fill="black", anchor=anchor,
                             stroke_width=sw, stroke_fill="black")


def crop_shift(img, side, mm, dpi):
    """Recorta `mm` del borde `side` ('l','r','t','b') y desliza el contenido
    hacia ese borde; el tamano de la imagen no cambia."""
    px = round(mm / 25.4 * dpi)
    if px <= 0:
        return img
    w, h = img.size
    px = min(px, (w if side in "lr" else h) - 1)
    box, pos = {"l": ((px, 0, w, h), (0, 0)), "r": ((0, 0, w - px, h), (px, 0)),
                "t": ((0, px, w, h), (0, 0)), "b": ((0, 0, w, h - px), (0, px))}[side]
    out = Image.new("RGB", (w, h), "white")
    out.paste(img.crop(box), pos)
    return out


# -------------------------------------------------------------------- marcas
MARK_COLOR = (70, 70, 70)


def _dashed(draw, p0, p1, dpi, width):
    """Linea punteada horizontal o vertical (p1 > p0)."""
    dash, gap = round(3 / 25.4 * dpi), round(2 / 25.4 * dpi)
    (x0, y0), (x1, y1) = p0, p1
    length = max(abs(x1 - x0), abs(y1 - y0))
    pos = 0
    while pos < length:
        end = min(pos + dash, length)
        if x0 == x1:
            draw.line([(x0, y0 + pos), (x0, y0 + end)], fill=MARK_COLOR, width=width)
        else:
            draw.line([(x0 + pos, y0), (x0 + end, y0)], fill=MARK_COLOR, width=width)
        pos += dash + gap


def draw_center_marks(d, W, H, orient, style, dpi):
    """orient 'v' = linea vertical en el centro; 'h' = horizontal."""
    if style == "ninguna":
        return
    width = max(1, round(dpi / 250))
    tick = round(6 / 25.4 * dpi)
    if orient == "v":
        x = W // 2
        if style == "linea":
            _dashed(d, (x, 0), (x, H - 1), dpi, width)
        else:
            d.line([(x, 0), (x, tick)], fill=MARK_COLOR, width=width)
            d.line([(x, H - 1 - tick), (x, H - 1)], fill=MARK_COLOR, width=width)
    else:
        y = H // 2
        if style == "linea":
            _dashed(d, (0, y), (W - 1, y), dpi, width)
        else:
            d.line([(0, y), (tick, y)], fill=MARK_COLOR, width=width)
            d.line([(W - 1 - tick, y), (W - 1, y)], fill=MARK_COLOR, width=width)


def draw_page_borders(d, rects, style, dpi):
    """Marca el borde de cada pagina original (esquinas o contorno)."""
    if style == "ninguna":
        return
    width = max(1, round(dpi / 250))
    L = round(5 / 25.4 * dpi)
    for x, y, w, h in rects:
        x2, y2 = x + w - 1, y + h - 1
        if style == "contorno":
            _dashed(d, (x, y), (x2, y), dpi, width)
            _dashed(d, (x, y2), (x2, y2), dpi, width)
            _dashed(d, (x, y), (x, y2), dpi, width)
            _dashed(d, (x2, y), (x2, y2), dpi, width)
        else:
            for cx, cy, sx, sy in ((x, y, 1, 1), (x2, y, -1, 1), (x, y2, 1, -1), (x2, y2, -1, -1)):
                d.line([(cx, cy), (cx + sx * L, cy)], fill=MARK_COLOR, width=width)
                d.line([(cx, cy), (cx, cy + sy * L)], fill=MARK_COLOR, width=width)


# ------------------------------------------------------------- imposicion
def imposition_order(n, per=None):
    """n multiplo de 4 -> [((frente_1, frente_2), (reverso_1, reverso_2)), ...]
    per = paginas por cuadernillo (multiplo de 4 que divide a n). None = un solo
    cuadernillo con todo el documento; per=4 = cuadernillos de una hoja (multi)."""
    per = per or n
    out = []
    for base in range(0, n, per):
        for i in range(per // 4):
            out.append(((base + per - 2 * i, base + 2 * i + 1),
                        (base + 2 * i + 2, base + per - 2 * i - 1)))
    return out


def pad_pages(total, keep_back_cover):
    """Lista de indices (1-based); None = pagina en blanco de relleno."""
    pages = list(range(1, total + 1))
    missing = (-total) % 4
    if missing:
        if keep_back_cover and total > 1:
            pages = pages[:-1] + [None] * missing + pages[-1:]
        else:
            pages = pages + [None] * missing
    return pages


def make_layout(mode, spine, sheet, dpi, pw_in, ph_in):
    """Geometria de la hoja. 'spreads' = pares de posiciones (primera, segunda);
    'copies' = posiciones de copias identicas (modos dup)."""
    sw, sh = SHEETS[sheet]
    hspread = spine != "superior"    # paginas lado a lado (False = una sobre otra)
    if mode in ("sencillo", "multi"):
        landscape, cols, rows = hspread, (2 if hspread else 1), (1 if hspread else 2)
    elif mode == "bolsillo":
        landscape, cols, rows = (not hspread), 2, 2
    else:  # dup2 / dup4: orientacion de hoja segun cual aproveche mejor la pagina
        def fit(land):
            Wi, Hi = (sh, sw) if land else (sw, sh)
            c, r = ((2, 1) if land else (1, 2)) if mode == "dup2" else (2, 2)
            return min(Wi / c / pw_in, Hi / r / ph_in)
        landscape = fit(True) >= fit(False) if mode == "dup2" else fit(True) > fit(False)
        cols, rows = ((2, 1) if landscape else (1, 2)) if mode == "dup2" else (2, 2)
    Wi, Hi = (sh, sw) if landscape else (sw, sh)
    W, H = round(Wi * dpi), round(Hi * dpi)
    slot_w, slot_h = W // cols, H // rows
    pos = lambda c, r: (c * slot_w, r * slot_h)
    lay = {"W": W, "H": H, "slot_w": slot_w, "slot_h": slot_h, "spreads": [], "copies": [],
           "fold": None, "cut": []}
    if mode in ("sencillo", "multi"):
        lay["spreads"] = [[pos(0, 0), pos(1, 0)]] if hspread else [[pos(0, 0), pos(0, 1)]]
    elif mode == "bolsillo":
        lay["spreads"] = ([[pos(0, r), pos(1, r)] for r in range(2)] if hspread
                          else [[pos(c, 0), pos(c, 1)] for c in range(2)])
    else:
        lay["copies"] = [pos(c, r) for r in range(rows) for c in range(cols)]
    if mode in IMPOSED:
        lay["fold"] = "v" if hspread else "h"
    if mode == "bolsillo":
        lay["cut"] = ["h" if hspread else "v"]
    elif mode == "dup2":
        lay["cut"] = ["v" if cols == 2 else "h"]
    elif mode == "dup4":
        lay["cut"] = ["v", "h"]
    return lay


def plan_text(total, mode="sencillo", keep_back=False, spine="izquierda"):
    if mode == "dup2":
        return "\n".join(T("plan_dup2", k=k, p=k) for k in range(1, total + 1))
    if mode == "dup4":
        return "\n".join(T("plan_dup4", k=k, p=k) for k in range(1, total + 1))
    if mode == "sin":
        return "\n".join(T("plan_sin", k=k, p=k) for k in range(1, total + 1))
    order = pad_pages(total, keep_back)
    lab = lambda t: " / ".join(
        T("blank") if order[p - 1] is None else str(order[p - 1]) for p in t)
    lines = []
    for k, (f, b) in enumerate(imposition_order(len(order), 4 if mode == "multi" else None), 1):
        if spine == "derecha":
            f, b = f[::-1], b[::-1]
        lines.append(T("plan_line", k=k, f=lab(f), b=lab(b)))
    return "\n".join(lines)


PDF_LOCK = threading.Lock()   # pdfium no es seguro entre hilos
PREVIEW_DPI = 72
PREVIEW_LIMIT = 40            # caras maximas en la vista previa


class Job:
    """Genera, una por una, las caras de salida (hojas ya maquetadas)."""

    def __init__(self, pdf, mode, sheet, dpi, inset_mm, keep_back, gray,
                 num=None, marks=None, spine="izquierda", crop_in=0.0, crop_out=0.0):
        if mode not in MODES:
            raise ValueError(f"mode? {mode}")
        if spine not in SPINES:
            raise ValueError(f"spine? {spine}")
        self.pdf, self.total = pdf, len(pdf)
        if self.total == 0:
            raise ValueError(T("err_nopages"))
        self.mode, self.dpi, self.gray, self.spine = mode, dpi, gray, spine
        self.crop_in, self.crop_out = crop_in, crop_out
        self.num = {**NUM_DEFAULT, **(num or {})}
        self.marks = {**MARKS_DEFAULT, **(marks or {})}
        self.num_on = bool(self.num["activar"])
        self.last = self.total
        if self.num_on:
            self.num["desde"] = max(1, min(int(self.num["desde"]), self.total))
            last = int(self.num["hasta"]) or self.total
            self.last = max(self.num["desde"], min(last, self.total))
        self.font_cache, self.min_fit, self._first = {}, 1.0, True
        self.inset_px = round(inset_mm / 25.4 * dpi)
        pw, ph = pdf[0].get_size()
        self.lay = None if mode == "sin" else make_layout(mode, spine, sheet, dpi, pw / 72, ph / 72)
        self.order, self.plan, self.n, self.sig = [], [], 0, 0
        if mode in IMPOSED:
            self.order = pad_pages(self.total, keep_back)
            self.n = len(self.order)
            self.plan = imposition_order(self.n, 4 if mode == "multi" else None)
            self.sig = 4 if mode == "multi" else self.n   # paginas por cuadernillo
            if spine == "derecha":      # lectura de derecha a izquierda
                self.plan = [(f[::-1], b[::-1]) for f, b in self.plan]
        self.count = len(self.plan) * 2 if mode in IMPOSED else self.total

    def font_warn(self):
        if self.num_on and self.font_cache and not all(v[2] for v in self.font_cache.values()):
            return T("warn_font", f=self.num["fuente"])
        return ""

    def prep(self, p):
        """Rasteriza la pagina p (1-based), recorta margenes y numera."""
        page, dpi, lay = self.pdf[p - 1], self.dpi, self.lay
        if lay is None:       # sin maquetado: tamano original 1:1
            img, fit = page.render(scale=dpi / 72).to_pil().convert("RGB"), 1.0
        else:
            w, h = page.get_size()
            fit = min((lay["slot_w"] - 2 * self.inset_px) / (w / 72 * dpi),
                      (lay["slot_h"] - 2 * self.inset_px) / (h / 72 * dpi))
            img = page.render(scale=dpi / 72 * fit).to_pil().convert("RGB")
        self.min_fit = fit if self._first else min(self.min_fit, fit)
        self._first = False
        inner, outer = page_edges(p, self.spine)
        img = crop_shift(img, inner, self.crop_in, dpi)
        img = crop_shift(img, outer, self.crop_out, dpi)
        if self.num_on and self.num["desde"] <= p <= self.last:
            draw_number(img, p, self.num, dpi, self.font_cache, self.spine)
        return img

    def paste(self, canvas, img, slot_xy, rects, rotate=False):
        x = slot_xy[0] + (self.lay["slot_w"] - img.width) // 2
        y = slot_xy[1] + (self.lay["slot_h"] - img.height) // 2
        canvas.paste(img.rotate(180) if rotate else img, (x, y))
        rects.append((x, y, img.width, img.height))

    def finish(self, canvas, rects, fold_on):
        d, lay, mk = ImageDraw.Draw(canvas), self.lay, self.marks
        if lay["fold"] and fold_on:
            draw_center_marks(d, canvas.width, canvas.height, lay["fold"], mk["pliegue"], self.dpi)
        for orient in lay["cut"]:
            draw_center_marks(d, canvas.width, canvas.height, orient, mk["corte"], self.dpi)
        draw_page_borders(d, rects, mk["borde"], self.dpi)
        return canvas.convert("L") if self.gray else canvas

    def sheets(self, limit=None):
        """Genera (imagen, meta); meta = {sheet, side, pages}."""
        made, lay = 0, self.lay
        if self.mode in IMPOSED:
            for k, sides in enumerate(self.plan):
                fold_on = (self.marks["pliegue_hojas"] == "todas") or k in (0, len(self.plan) - 1)
                for si, pair in enumerate(sides):
                    canvas = Image.new("RGB", (lay["W"], lay["H"]), "white")
                    rects, imgs = [], {}
                    for spread in lay["spreads"]:
                        for slot_xy, position in zip(spread, pair):
                            p = self.order[position - 1]
                            if p is None:
                                continue
                            if p not in imgs:
                                imgs[p] = self.prep(p)
                            # lomo superior: la mitad "de atras" va girada 180 grados
                            self.paste(canvas, imgs[p], slot_xy, rects,
                                       rotate=(self.spine == "superior" and (position - 1) % self.sig >= self.sig // 2))
                    yield (self.finish(canvas, rects, fold_on),
                           {"sheet": k + 1, "side": ("front", "back")[si],
                            "pages": [self.order[pos - 1] for pos in pair]})
                    made += 1
                    if limit and made >= limit:
                        return
        elif self.mode in ("dup2", "dup4"):
            for p in range(1, self.total + 1):
                canvas = Image.new("RGB", (lay["W"], lay["H"]), "white")
                rects, img0 = [], self.prep(p)
                for slot_xy in lay["copies"]:
                    self.paste(canvas, img0, slot_xy, rects)
                yield self.finish(canvas, rects, False), {"sheet": p, "side": "page", "pages": [p]}
                made += 1
                if limit and made >= limit:
                    return
        else:  # sin maquetado
            for p in range(1, self.total + 1):
                img = self.prep(p)
                draw_page_borders(ImageDraw.Draw(img), [(0, 0, img.width, img.height)],
                                  self.marks["borde"], self.dpi)
                yield (img.convert("L") if self.gray else img,
                       {"sheet": p, "side": "page", "pages": [p]})
                made += 1
                if limit and made >= limit:
                    return

    def spreads(self, limit=None):
        """Resultado esperado: el documento ya doblado, en orden de lectura."""
        made, lay = 0, self.lay
        if self.mode in IMPOSED:
            n, hs = self.n, self.spine != "superior"
            sw, sh = lay["slot_w"], lay["slot_h"]
            pairs = [(0, 1)] + [(p, p + 1) for p in range(2, n, 2)] + [(n, 0)]
            if self.spine == "derecha":        # lectura de derecha a izquierda
                pairs = [(b, a) for a, b in pairs]
            for a, b in pairs:
                canvas = Image.new("RGB", (2 * sw, sh) if hs else (sw, 2 * sh), "white")
                d = ImageDraw.Draw(canvas)
                d.line([(sw, 0), (sw, sh)] if hs else [(0, sh), (sw, sh)], fill=(215, 215, 215))
                labels = []
                for k, pos in enumerate((a, b)):
                    if pos == 0:               # fuera del libro (guarda / contraguarda)
                        labels.append(0)
                        continue
                    p = self.order[pos - 1]
                    labels.append(p)
                    if p is None:
                        continue
                    img = self.prep(p)
                    ox, oy = (k * sw, 0) if hs else (0, k * sh)
                    canvas.paste(img, (ox + (sw - img.width) // 2, oy + (sh - img.height) // 2))
                yield canvas, {"view": "result", "sheet": made + 1, "side": "spread", "pages": labels}
                made += 1
                if limit and made >= limit:
                    return
        else:
            for p in range(1, self.total + 1):
                yield self.prep(p), {"view": "result", "sheet": p, "side": "page", "pages": [p]}
                made += 1
                if limit and made >= limit:
                    return


def build(src, dst, mode, sheet, dpi, inset_mm, keep_back, gray, quality,
          verbose=True, log=print, progress=None, num=None, marks=None,
          spine="izquierda", crop_in=0.0, crop_out=0.0):
    with PDF_LOCK:
        pdf = pdfium.PdfDocument(src)
        job = Job(pdf, mode, sheet, dpi, inset_mm, keep_back, gray, num, marks, spine,
                  crop_in, crop_out)
        if verbose:
            if mode in IMPOSED:
                log(T("log_pages", t=job.total, n=job.n, h=job.n // 4, c=job.n // 2))
            else:
                log(T("log_pages1", t=job.total))
        out = MiniPDF(dst)
        try:
            for i, (img, _meta) in enumerate(job.sheets(), 1):
                out.add_page(jpeg_bytes(img, quality, dpi), img.width, img.height, gray, dpi)
                if progress:
                    progress(i / job.count)
        finally:
            out.close()
    warn = job.font_warn()
    if verbose:
        lay, nm = job.lay, job.num
        log(T("log_cfg", s=sheet if lay else "-", m=T("mode_" + mode),
              sp=T("opt_" + spine), d=dpi))
        log(plan_text(job.total, mode, keep_back, spine))
        if job.num_on:
            log("\n" + T("log_num", a=nm["desde"], b=job.last, i=nm["inicio"], t=nm["tam"],
                         font=nm["fuente"], bold=T("bold_word") if nm["negrita"] else "",
                         v=nm["vert"], h=nm["horiz"]))
            if warn:
                log(warn)
        log("\n" + T("log_scale", p=f"{job.min_fit * 100:.0f}"))
        if lay:
            log(T("log_slot", w=lay["slot_w"] / dpi, h=lay["slot_h"] / dpi,
                  wm=lay["slot_w"] / dpi * 25.4, hm=lay["slot_h"] / dpi * 25.4))
        log("\n" + T("log_print"))
        log("  " + T(tip_key(mode)))
        log("\n" + T("log_done", dst=dst))
    return warn


# ------------------------------------------------------------- vista previa
ZOOMS = [40, 60, 80, 100, 150]


def make_preview(src, mode, sheet, inset_mm, keep_back, gray, num=None, marks=None,
                 spine="izquierda", crop_in=0.0, crop_out=0.0, limit=PREVIEW_LIMIT, view="print"):
    """Genera las primeras `limit` vistas a baja resolucion.
    view 'print' = hojas como se imprimen; 'result' = documento ya doblado (por pliegos).
    Devuelve ([(imagen, meta)], total)."""
    with PDF_LOCK:
        pdf = pdfium.PdfDocument(src)
        job = Job(pdf, mode, sheet, PREVIEW_DPI, inset_mm, keep_back, gray, num, marks,
                  spine, crop_in, crop_out)
        if view == "result":
            total = (job.n // 2 + 1) if mode in IMPOSED else job.total
            return list(job.spreads(limit)), total
        return list(job.sheets(limit)), job.count


def preview_caption(meta, imposed):
    if meta.get("view") == "result":
        parts = ["–" if p == 0 else (T("blank") if p is None else str(p)) for p in meta["pages"]]
        return "  |  ".join(parts)
    label = T("prev_sheet", k=meta["sheet"])
    pages = " / ".join(T("blank") if p is None else str(p) for p in meta["pages"])
    if imposed:
        side = T("prev_front") if meta["side"] == "front" else T("prev_back")
        return f"{label} · {side}:  {pages}"
    return f"{label}:  {pages}"


def layout_items(sizes, imposed, avail_w, gap=14, cap_h=22):
    """Posiciona miniaturas en una cuadricula. Devuelve (posiciones, ancho, alto)."""
    if not sizes:
        return [], gap, gap
    cw = max(w for w, _ in sizes)
    cols = 2 if imposed else max(1, (avail_w - gap) // (cw + gap))
    row_h = [0] * (-(-len(sizes) // cols))
    for i, (_, h) in enumerate(sizes):
        row_h[i // cols] = max(row_h[i // cols], h)
    ys, y = [], gap
    for rh in row_h:
        ys.append(y)
        y += rh + cap_h + gap
    pos = [(gap + (i % cols) * (cw + gap), ys[i // cols]) for i in range(len(sizes))]
    return pos, gap + cols * (cw + gap), y


def preview_png(items, imposed, path, avail_w=900):
    """Version de consola de la vista previa: guarda una imagen PNG."""
    sizes = [(im.width, im.height) for im, _ in items]
    pos, tw, th = layout_items(sizes, imposed, avail_w)
    canvas = Image.new("RGB", (tw, th), (200, 200, 200))
    d = ImageDraw.Draw(canvas)
    for (im, meta), (x, y) in zip(items, pos):
        canvas.paste(im.convert("RGB"), (x, y))
        d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=(110, 110, 110))
        d.text((x, y + im.height + 4), preview_caption(meta, imposed), fill=(0, 0, 0))
    canvas.save(path)


def tip_key(mode):
    return {"sencillo": "tip_short", "bolsillo": "tip_long", "multi": "tip_multi", "dup2": "tip_dup2",
            "dup4": "tip_dup4", "sin": "tip_sin"}[mode]


# ------------------------------------------------------------------ interfaz
def find_icon():
    here = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    for d in (here, os.getcwd()):
        p = os.path.join(d, ICON_NAME)
        if os.path.isfile(p):
            return p
    return None


def interactive():
    print(f"=== Malvin v{__version__} ===\n")
    path = input("PDF (drag & drop / path): ").strip().strip('"')
    m = alias_mode(input(f"Mode {MODES} [sencillo]: ").strip() or "sencillo")
    s = input(f"Sheet {SHEET_KEYS} [carta]: ").strip().lower() or "carta"
    return path, m, s


PALETTES = {
    "light": dict(bg="#f3f3f3", field="#ffffff", fg="#1a1a1a", sub="#5f5f5f", border="#cfcfcf",
                  btn="#fbfbfb", btn_hover="#f0f0f0", btn_press="#e5e5e5", tab_idle="#e6e6e6",
                  accent="#0067c0", accent_fg="#ffffff", go="#a8e6b5", go_hover="#93dca3",
                  go_press="#7fd091", go_fg="#0d3b1a", go_dis="#d9e6dc", go_bar="#4cc46a",
                  canvas="#e3e3e3", img_border="#8a8a8a", tip_bg="#ffffe1", tip_fg="#1a1a1a",
                  scroll="#c2c2c2", trough="#e6e6e6", sel="#cce4f7"),
    "dark": dict(bg="#202020", field="#2d2d2d", fg="#f0f0f0", sub="#a8a8a8", border="#474747",
                 btn="#2f2f2f", btn_hover="#3a3a3a", btn_press="#444444", tab_idle="#2a2a2a",
                 accent="#60cdff", accent_fg="#00253d", go="#3c8f55", go_hover="#46a463",
                 go_press="#34804b", go_fg="#ffffff", go_dis="#34403a", go_bar="#58c878",
                 canvas="#161616", img_border="#777777", tip_bg="#2b2b2b", tip_fg="#f0f0f0",
                 scroll="#5a5a5a", trough="#2a2a2a", sel="#0a4a73"),
}


def system_theme():
    """'light' u 'dark' segun la configuracion de Windows (claro si no se puede saber)."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value else "dark"
    except Exception:
        return "light"


def gui():
    try:  # Windows: nitidez en pantallas de alta resolucion (antes de crear la ventana)
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter import font as tkfont
    try:
        from PIL import ImageTk
    except Exception:
        ImageTk = None

    try:  # Windows: que la barra de tareas use el icono de Malvin y no el de Python
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Malvin.MaquetadoAutomatico.1")
    except Exception:
        pass

    root = tk.Tk()
    try:
        S = max(1.0, float(root.winfo_fpixels("1i")) / 96.0)
    except Exception:
        S = 1.0

    def px(n):
        return int(round(n * S))

    root.geometry(f"{px(1240)}x{px(800)}")
    root.minsize(px(980), px(640))
    icon = find_icon()
    if icon:
        try:  # esquina de la ventana + barra de tareas
            root.iconbitmap(default=icon)
        except Exception:
            pass

    for fname in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
        try:
            tkfont.nametofont(fname).configure(family="Segoe UI", size=10)
        except Exception:
            pass

    def G(key, **kw):
        """Texto para widgets (arabe/persa: con union de letras si hay librerias)."""
        return shape(T(key, **kw))

    # ------------------------------------------------------------ variables
    v_in, v_out = tk.StringVar(), tk.StringVar()
    v_mode = tk.StringVar(value="sencillo")
    v_spine = tk.StringVar(value="izquierda")
    v_sheet = tk.StringVar(value="carta")
    v_dpi = tk.IntVar(value=300)
    v_inset = tk.DoubleVar(value=0.0)
    v_keep = tk.BooleanVar(value=False)       # contraportada: desactivada por defecto
    v_gray = tk.BooleanVar(value=False)
    v_info = tk.StringVar(value="")
    v_status = tk.StringVar(value="")
    v_view = tk.StringVar(value="print")      # print | result
    v_theme = tk.StringVar(value="auto")
    v_crop_in, v_crop_out = tk.DoubleVar(value=0.0), tk.DoubleVar(value=0.0)
    v_fold = tk.StringVar(value="ninguna")
    v_fold_where = tk.StringVar(value="extremos")
    v_cut = tk.StringVar(value="marcas")
    v_border = tk.StringVar(value="ninguna")
    n_on = tk.BooleanVar(value=False)
    n_desde, n_inicio, n_hasta = tk.IntVar(value=1), tk.IntVar(value=1), tk.IntVar(value=0)
    n_tam = tk.DoubleVar(value=12.0)
    n_fuente = tk.StringVar(value="Arial")
    n_bold = tk.BooleanVar(value=False)
    n_vert, n_horiz = tk.StringVar(value="inferior"), tk.StringVar(value="centro")
    n_mv, n_mh = tk.DoubleVar(value=10.0), tk.DoubleVar(value=15.0)
    n_formato = tk.StringVar(value="{n}")
    lang_names = [shape(n, c in RTL_LANGS) for c, n in LANGS.items()]
    name_to_code = dict(zip(lang_names, LANGS.keys()))
    v_lang_name = tk.StringVar(value=shape(LANGS.get(LANG, "English"), LANG in RTL_LANGS))
    W = {}                 # widgets que se recrean al cambiar de idioma o de tema
    P = dict(PALETTES["light"])
    pv = {"items": [], "token": 0, "after": None, "photos": [], "imposed": False,
          "view": "print", "h": 0, "rafter": None}

    # ---------------------------------------------------------------- tema
    def apply_theme():
        name = v_theme.get()
        if name == "auto":
            name = system_theme()
        P.clear()
        P.update(PALETTES[name])
        root.configure(background=P["bg"])
        st = ttk.Style(root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        base = ("Segoe UI", 10)
        st.configure(".", background=P["bg"], foreground=P["fg"], bordercolor=P["border"],
                     lightcolor=P["bg"], darkcolor=P["bg"], troughcolor=P["trough"],
                     focuscolor=P["bg"], font=base)
        st.configure("TLabel", background=P["bg"], foreground=P["fg"])
        st.configure("Hint.TLabel", background=P["bg"], foreground=P["sub"])
        st.configure("TFrame", background=P["bg"])
        st.configure("TLabelframe", background=P["bg"], bordercolor=P["border"],
                     lightcolor=P["border"], darkcolor=P["border"], borderwidth=1, relief="solid")
        st.configure("TLabelframe.Label", background=P["bg"], foreground=P["sub"],
                     font=("Segoe UI", 10, "bold"))
        st.configure("TSeparator", background=P["border"])
        st.configure("TButton", padding=(px(14), px(6)), background=P["btn"], foreground=P["fg"],
                     bordercolor=P["border"], lightcolor=P["btn"], darkcolor=P["btn"],
                     relief="flat", focuscolor=P["btn"])
        st.map("TButton", background=[("disabled", P["bg"]), ("pressed", P["btn_press"]),
                                      ("active", P["btn_hover"])],
               foreground=[("disabled", P["sub"])], bordercolor=[("focus", P["accent"])])
        st.configure("Go.TButton", padding=(px(28), px(10)), font=("Segoe UI", 11, "bold"),
                     background=P["go"], foreground=P["go_fg"], bordercolor=P["go_press"],
                     lightcolor=P["go"], darkcolor=P["go"], relief="flat", focuscolor=P["go"])
        st.map("Go.TButton", background=[("disabled", P["go_dis"]), ("pressed", P["go_press"]),
                                         ("active", P["go_hover"])],
               foreground=[("disabled", P["sub"])])
        for name_ in ("TEntry", "TCombobox", "TSpinbox"):
            st.configure(name_, fieldbackground=P["field"], background=P["btn"], foreground=P["fg"],
                         bordercolor=P["border"], lightcolor=P["border"], darkcolor=P["border"],
                         insertcolor=P["fg"], arrowcolor=P["fg"], padding=px(4),
                         selectbackground=P["sel"], selectforeground=P["fg"])
        st.map("TCombobox", fieldbackground=[("readonly", P["field"]), ("disabled", P["bg"])],
               foreground=[("disabled", P["sub"])],
               selectbackground=[("readonly", P["field"])],
               selectforeground=[("readonly", P["fg"])],
               bordercolor=[("focus", P["accent"])])
        st.map("TEntry", bordercolor=[("focus", P["accent"])])
        st.map("TSpinbox", bordercolor=[("focus", P["accent"])],
               fieldbackground=[("disabled", P["bg"])])
        root.option_add("*TCombobox*Listbox.background", P["field"])
        root.option_add("*TCombobox*Listbox.foreground", P["fg"])
        root.option_add("*TCombobox*Listbox.selectBackground", P["sel"])
        root.option_add("*TCombobox*Listbox.selectForeground", P["fg"])
        root.option_add("*TCombobox*Listbox.font", base)
        for name_ in ("TCheckbutton", "TRadiobutton"):
            st.configure(name_, background=P["bg"], foreground=P["fg"],
                         indicatorbackground=P["field"], indicatorforeground=P["accent"])
            st.map(name_, background=[("active", P["bg"])],
                   indicatorbackground=[("pressed", P["btn_press"]), ("disabled", P["bg"])],
                   foreground=[("disabled", P["sub"])])
        st.configure("TNotebook", background=P["bg"], borderwidth=0, tabmargins=(0, px(2), 0, 0))
        st.configure("TNotebook.Tab", padding=(px(16), px(7)), background=P["tab_idle"],
                     foreground=P["sub"], borderwidth=0, lightcolor=P["tab_idle"],
                     darkcolor=P["tab_idle"], bordercolor=P["tab_idle"])
        st.map("TNotebook.Tab", background=[("selected", P["bg"]), ("active", P["btn_hover"])],
               foreground=[("selected", P["fg"])])
        st.configure("Go.Horizontal.TProgressbar", troughcolor=P["trough"], background=P["go_bar"],
                     bordercolor=P["bg"], lightcolor=P["go_bar"], darkcolor=P["go_bar"],
                     thickness=px(8))
        st.configure("TScrollbar", background=P["scroll"], troughcolor=P["trough"],
                     bordercolor=P["trough"], arrowcolor=P["fg"], lightcolor=P["scroll"],
                     darkcolor=P["scroll"], gripcount=0, arrowsize=px(14))
        st.map("TScrollbar", background=[("active", P["sub"])])
        try:  # barra de titulo oscura en Windows 10/11
            import ctypes
            root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            val = ctypes.c_int(1 if name == "dark" else 0)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), 4)
        except Exception:
            pass

    class Tip:
        """Leyenda emergente tras mantener el puntero un momento sobre el widget."""

        def __init__(self, widget, text_fn, delay=700):
            self.w, self.fn, self.delay, self.win, self.job = widget, text_fn, delay, None, None
            widget.bind("<Enter>", self.enter, add="+")
            widget.bind("<Leave>", self.hide, add="+")
            widget.bind("<ButtonPress>", self.hide, add="+")

        def enter(self, _e=None):
            self.hide()
            self.job = self.w.after(self.delay, self.show)

        def show(self):
            self.job = None
            text = self.fn()
            if not text:
                return
            self.win = tk.Toplevel(self.w)
            self.win.wm_overrideredirect(True)
            self.win.wm_geometry(f"+{self.w.winfo_rootx() + px(16)}+"
                                 f"{self.w.winfo_rooty() + self.w.winfo_height() + px(6)}")
            tk.Label(self.win, text=text, justify="left", wraplength=px(380),
                     background=P["tip_bg"], foreground=P["tip_fg"], relief="solid",
                     borderwidth=1, padx=px(8), pady=px(5)).pack()

        def hide(self, _e=None):
            if self.job:
                self.w.after_cancel(self.job)
                self.job = None
            if self.win:
                self.win.destroy()
                self.win = None

    # ------------------------------------------------------------- utilidades
    def keyed_combo(parent, keyvar, keys, prefix, width=14, on_change=None):
        labels = [G(prefix + k) for k in keys]
        disp = tk.StringVar(value=G(prefix + keyvar.get()))
        cb = ttk.Combobox(parent, textvariable=disp, values=labels, state="readonly", width=width)

        def sel(_e=None):
            keyvar.set(keys[labels.index(disp.get())])
            if on_change:
                on_change()
            cb.selection_clear()
        cb.bind("<<ComboboxSelected>>", sel)
        return cb

    def default_out(p):
        return os.path.splitext(p)[0] + f"_malvin_{v_mode.get()}.pdf"

    def refresh_info(*_):
        path = v_in.get().strip()
        if not os.path.isfile(path):
            v_info.set(G("info_pick"))
            return
        if not PDF_LOCK.acquire(blocking=False):   # hay un proceso usando pdfium
            return
        try:
            n = len(pdfium.PdfDocument(path))
            if v_mode.get() in IMPOSED:
                h = -(-n // 4)
                v_info.set(G("info_pages", n=n, h=h, c=h * 2))
            else:
                v_info.set(G("info_pages1", n=n))
        except Exception as e:
            v_info.set(G("err_read", e=e))
        finally:
            PDF_LOCK.release()

    def update_states():
        imposed = v_mode.get() in IMPOSED
        if W.get("sheet_cb") is not None:
            W["sheet_cb"].configure(state="readonly" if v_mode.get() != "sin" else "disabled")
        if W.get("back_chk") is not None:
            W["back_chk"].configure(state="normal" if imposed else "disabled")

    def on_mode():
        if v_in.get().strip():
            v_out.set(default_out(v_in.get().strip()))
        update_states()

    def pick_in():
        p = filedialog.askopenfilename(title="PDF", filetypes=[("PDF", "*.pdf")])
        if p:
            v_in.set(p)
            v_out.set(default_out(p))

    def pick_out():
        p = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if p:
            v_out.set(p)

    def pick_font():
        p = filedialog.askopenfilename(filetypes=[("Fonts", "*.ttf *.otf *.ttc")])
        if p:
            n_fuente.set(p)

    def spin(parent, var, a, b, inc=1, w=7):
        return ttk.Spinbox(parent, from_=a, to=b, increment=inc, textvariable=var, width=w)

    # --------------------------------------------------------- vista previa
    def clear_canvas():
        cv = W.get("cv")
        if cv is not None:
            cv.delete("all")
        pv["photos"] = []

    def render(_e=None):
        cv = W.get("cv")
        if cv is None:
            return
        clear_canvas()
        items = pv["items"]
        ch = max(cv.winfo_height(), px(200))
        pv["h"] = ch
        if not items or ImageTk is None:
            cv.create_text(px(20), ch // 2, anchor="w", fill=P["sub"],
                           text=G("info_pick") if ImageTk is not None else "Pillow ImageTk?")
            cv.configure(scrollregion=(0, 0, 0, ch))
            return
        cap, x = px(36), px(14)
        avail = ch - cap - px(18)
        for im, meta in items:
            sc = min(avail / im.height, 1.8)
            w, h = max(1, round(im.width * sc)), max(1, round(im.height * sc))
            img = im if (w, h) == im.size else im.resize((w, h), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            pv["photos"].append(ph)            # evita que Tk los descarte
            y = px(10)
            cv.create_image(x, y, image=ph, anchor="nw")
            cv.create_rectangle(x - 1, y - 1, x + w, y + h, outline=P["img_border"])
            cv.create_text(x + w // 2, y + h + px(8), anchor="n", fill=P["fg"], width=w + px(10),
                           justify="center",
                           text=shape(preview_caption(meta, pv["imposed"] and pv["view"] == "print")))
            x += w + px(16)
        cv.configure(scrollregion=(0, 0, x, ch))
        cv.xview_moveto(0)

    def on_canvas_resize(_e=None):
        cv = W.get("cv")
        if cv is None or abs(cv.winfo_height() - pv["h"]) < 4:
            return
        if pv["rafter"]:
            root.after_cancel(pv["rafter"])
        pv["rafter"] = root.after(150, render)

    def show(tok, items, count, view, mode):
        if tok != pv["token"]:
            return
        pv["items"], pv["imposed"], pv["view"] = items, mode in IMPOSED, view
        msg = ""
        if view == "print":
            tot = count // 2 if pv["imposed"] else count
            got = len(items) // 2 if pv["imposed"] else len(items)
            if got < tot:
                msg = G("prev_limit", m=got, n=tot)
        elif len(items) < count:
            msg = G("prev_limit2", m=len(items), n=count)
        v_status.set(msg)
        render()

    def show_error(tok, text):
        if tok == pv["token"]:
            v_status.set(T("err_prefix", e=text))

    def start_preview():
        pv["after"] = None
        if W.get("cv") is None:
            return
        c = collect(silent=True)
        if not c:
            if not os.path.isfile(v_in.get().strip()):
                pv["items"] = []
                v_status.set("")
                render()
            return
        args, kw = c
        src, _dst, mode, sheet, _dpi, inset, keep, gray, _q = args
        view = v_view.get()
        pv["token"] += 1
        tok = pv["token"]
        v_status.set(G("prev_loading"))

        def work():
            try:
                items, count = make_preview(src, mode, sheet, inset, keep, gray, limit=PREVIEW_LIMIT,
                                            view=view, **kw)
                root.after(0, show, tok, items, count, view, mode)
            except Exception as e:
                root.after(0, show_error, tok, str(e))

        threading.Thread(target=work, daemon=True).start()

    def schedule_preview(*_):
        if pv["after"]:
            root.after_cancel(pv["after"])
        pv["after"] = root.after(500, start_preview)

    # ------------------------------------------------------------- interfaz
    def change_lang(_=None):
        set_lang(name_to_code.get(v_lang_name.get(), "en"))
        build_ui()

    def build_ui():
        for w in root.winfo_children():
            w.destroy()
        apply_theme()
        root.title(G("title"))
        pad = {"padx": px(8), "pady": px(4)}

        # ---- barra superior: Maquetar (verde) + progreso + tema + idioma
        top = ttk.Frame(root)
        top.pack(fill="x", padx=px(14), pady=(px(12), px(4)))
        W["btn"] = ttk.Button(top, text=G("btn_run"), style="Go.TButton", command=run)
        W["btn"].pack(side="left")
        W["bar"] = ttk.Progressbar(top, maximum=1.0, style="Go.Horizontal.TProgressbar")
        W["bar"].pack(side="left", fill="x", expand=True, padx=px(16))
        lang_cb = ttk.Combobox(top, textvariable=v_lang_name, values=lang_names,
                               state="readonly", width=22)
        lang_cb.pack(side="right")
        lang_cb.bind("<<ComboboxSelected>>", change_lang)
        ttk.Label(top, text="🌐").pack(side="right", padx=(px(10), px(4)))
        keyed_combo(top, v_theme, ["auto", "light", "dark"], "theme_", 11,
                    lambda: build_ui()).pack(side="right")
        ttk.Label(top, text="◐").pack(side="right", padx=(px(10), px(4)))

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True, padx=px(14), pady=(px(4), px(14)))
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="ns")
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(px(14), 0))

        nb = ttk.Notebook(left)
        nb.pack(fill="both", expand=True)
        t1, t2, t3 = ttk.Frame(nb), ttk.Frame(nb), ttk.Frame(nb)
        nb.add(t1, text=G("tab_main"))
        nb.add(t2, text=G("tab_marks"))
        nb.add(t3, text=G("tab_num"))
        wrap = px(500)

        # ---- pestaña 1: archivos y estilo
        f = ttk.LabelFrame(t1, text=G("grp_files"))
        f.pack(fill="x", **pad)
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text=G("lbl_pdf")).grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=v_in, width=34).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(f, text=G("btn_browse"), command=pick_in).grid(row=0, column=2, **pad)
        ttk.Label(f, text=G("lbl_save")).grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(f, textvariable=v_out, width=34).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(f, text=G("btn_change"), command=pick_out).grid(row=1, column=2, **pad)
        ttk.Label(f, textvariable=v_info, style="Hint.TLabel").grid(row=2, column=1, sticky="w", **pad)

        o = ttk.LabelFrame(t1, text=G("grp_layout"))
        o.pack(fill="x", **pad)
        o.columnconfigure(1, weight=1)
        mode_cb = keyed_combo(o, v_mode, MODES, "mode_", 40, on_mode)
        mode_cb.grid(row=0, column=0, columnspan=4, sticky="ew", **pad)
        Tip(mode_cb, lambda: G("mode_" + v_mode.get() + "_d"))
        ttk.Label(o, text=G("lbl_spine")).grid(row=1, column=0, sticky="w", **pad)
        keyed_combo(o, v_spine, SPINES, "opt_", 12).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(o, text=G("lbl_sheet")).grid(row=2, column=0, sticky="w", **pad)
        W["sheet_cb"] = keyed_combo(o, v_sheet, SHEET_KEYS, "sheet_", 22)
        W["sheet_cb"].grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(o, text=G("lbl_dpi")).grid(row=2, column=2, sticky="e", **pad)
        spin(o, v_dpi, 100, 600, 50, 6).grid(row=2, column=3, sticky="w", **pad)
        ttk.Label(o, text=G("lbl_inset")).grid(row=3, column=0, sticky="w", **pad)
        spin(o, v_inset, 0, 20, 1, 6).grid(row=3, column=1, sticky="w", **pad)
        W["back_chk"] = ttk.Checkbutton(o, text=G("chk_backcover"), variable=v_keep)
        W["back_chk"].grid(row=4, column=0, columnspan=4, sticky="w", **pad)
        ttk.Checkbutton(o, text=G("chk_gray"), variable=v_gray).grid(
            row=5, column=0, columnspan=4, sticky="w", **pad)

        # ---- pestaña 2: margenes y marcas
        mg = ttk.Frame(t2)
        mg.pack(fill="x", **pad)
        ttk.Label(mg, text=G("lbl_crop_in")).grid(row=0, column=0, sticky="w", **pad)
        spin(mg, v_crop_in, 0, 50, 0.5, 6).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(mg, text=G("lbl_crop_out")).grid(row=1, column=0, sticky="w", **pad)
        spin(mg, v_crop_out, 0, 50, 0.5, 6).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(mg, text=G("hint_crop"), wraplength=wrap, style="Hint.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", **pad)
        ttk.Separator(mg).grid(row=3, column=0, columnspan=2, sticky="ew", pady=px(8))
        ttk.Label(mg, text=G("lbl_fold")).grid(row=4, column=0, sticky="w", **pad)
        keyed_combo(mg, v_fold, STYLE_OPTS, "opt_", 14).grid(row=4, column=1, sticky="w", **pad)
        ttk.Label(mg, text=G("lbl_fold_where")).grid(row=5, column=0, sticky="w", **pad)
        keyed_combo(mg, v_fold_where, WHERE_OPTS, "opt_", 18).grid(row=5, column=1, sticky="w", **pad)
        ttk.Label(mg, text=G("lbl_cut")).grid(row=6, column=0, sticky="w", **pad)
        keyed_combo(mg, v_cut, STYLE_OPTS, "opt_", 14).grid(row=6, column=1, sticky="w", **pad)
        ttk.Label(mg, text=G("lbl_border")).grid(row=7, column=0, sticky="w", **pad)
        keyed_combo(mg, v_border, BORDER_OPTS, "opt_", 14).grid(row=7, column=1, sticky="w", **pad)
        ttk.Label(mg, text=G("hint_marks"), wraplength=wrap, style="Hint.TLabel").grid(
            row=8, column=0, columnspan=2, sticky="w", **pad)

        # ---- pestaña 3: numeración
        nf = ttk.Frame(t3)
        nf.pack(fill="x", **pad)
        ttk.Checkbutton(nf, text=G("chk_num"), variable=n_on).grid(
            row=0, column=0, columnspan=4, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_from")).grid(row=1, column=0, sticky="w", **pad)
        spin(nf, n_desde, 1, 9999).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_call")).grid(row=1, column=2, sticky="e", **pad)
        spin(nf, n_inicio, -999, 9999).grid(row=1, column=3, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_to")).grid(row=2, column=0, sticky="w", **pad)
        spin(nf, n_hasta, 0, 9999).grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_fmt")).grid(row=2, column=2, sticky="e", **pad)
        ttk.Entry(nf, textvariable=n_formato, width=10).grid(row=2, column=3, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_font")).grid(row=3, column=0, sticky="w", **pad)
        ttk.Combobox(nf, textvariable=n_fuente, values=FONT_NAMES, width=22).grid(
            row=3, column=1, columnspan=2, sticky="w", **pad)
        ttk.Button(nf, text=G("btn_ttf"), command=pick_font).grid(row=3, column=3, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_size")).grid(row=4, column=0, sticky="w", **pad)
        spin(nf, n_tam, 4, 72).grid(row=4, column=1, sticky="w", **pad)
        ttk.Checkbutton(nf, text=G("chk_bold"), variable=n_bold).grid(row=4, column=2, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_vert")).grid(row=5, column=0, sticky="w", **pad)
        keyed_combo(nf, n_vert, VERT_OPTS, "opt_", 12).grid(row=5, column=1, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_horiz")).grid(row=5, column=2, sticky="e", **pad)
        keyed_combo(nf, n_horiz, HORIZ_OPTS, "opt_", 12).grid(row=5, column=3, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_mv")).grid(row=6, column=0, columnspan=2, sticky="w", **pad)
        spin(nf, n_mv, 0, 80, 1).grid(row=6, column=2, sticky="w", **pad)
        ttk.Label(nf, text=G("lbl_mh")).grid(row=7, column=0, columnspan=2, sticky="w", **pad)
        spin(nf, n_mh, 0, 80, 1).grid(row=7, column=2, sticky="w", **pad)
        ttk.Label(nf, text=G("hint_num"), wraplength=wrap, style="Hint.TLabel").grid(
            row=8, column=0, columnspan=4, sticky="w", **pad)

        # ---- panel derecho: vista previa (diseno de impresion / resultado esperado)
        pf = ttk.LabelFrame(right, text=G("grp_preview"))
        pf.pack(fill="both", expand=True)
        rb = ttk.Frame(pf)
        rb.pack(fill="x", padx=px(8), pady=(px(6), px(2)))
        ttk.Radiobutton(rb, text=G("view_print"), variable=v_view, value="print").pack(
            side="left", padx=(0, px(18)))
        ttk.Radiobutton(rb, text=G("view_result"), variable=v_view, value="result").pack(side="left")
        ttk.Label(pf, textvariable=v_status, style="Hint.TLabel").pack(
            fill="x", padx=px(10), pady=(0, px(2)))
        W["cv"] = tk.Canvas(pf, background=P["canvas"], highlightthickness=0,
                            height=px(380), xscrollincrement=px(40))
        hs = ttk.Scrollbar(pf, orient="horizontal", command=W["cv"].xview)
        W["cv"].configure(xscrollcommand=hs.set)
        W["cv"].pack(fill="both", expand=True, padx=px(8), pady=(px(2), 0))
        hs.pack(fill="x", padx=px(8), pady=(0, px(8)))

        def wheel(e):
            step = -1 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 1
            W["cv"].xview_scroll(step * 3, "units")
        W["cv"].bind("<MouseWheel>", wheel)
        W["cv"].bind("<Button-4>", wheel)
        W["cv"].bind("<Button-5>", wheel)
        W["cv"].bind("<Configure>", on_canvas_resize)

        update_states()
        refresh_info()
        if pv["items"]:
            root.after(80, render)
        else:
            schedule_preview()

    # ---------------------------------------------------------- generar PDF
    def done(ok, msg):
        W["btn"].configure(state="normal")
        W["bar"]["value"] = 1.0 if ok else 0
        (messagebox.showinfo if ok else messagebox.showerror)("Malvin", msg)

    def collect(silent=False):
        """Lee y valida las opciones. Devuelve (args, kw) o None."""
        src, dst = v_in.get().strip(), v_out.get().strip()
        if not os.path.isfile(src):
            if not silent:
                messagebox.showwarning("Malvin", T("msg_pick_pdf"))
            return None
        if not dst:
            dst = default_out(src)
            v_out.set(dst)
        try:
            num = {"activar": n_on.get(), "desde": int(n_desde.get()),
                   "inicio": int(n_inicio.get()), "hasta": int(n_hasta.get()),
                   "tam": float(n_tam.get()), "fuente": n_fuente.get(),
                   "negrita": n_bold.get(), "vert": n_vert.get(), "horiz": n_horiz.get(),
                   "margen_v": float(n_mv.get()), "margen_h": float(n_mh.get()),
                   "formato": n_formato.get() or "{n}"}
            marks = {"pliegue": v_fold.get(), "pliegue_hojas": v_fold_where.get(),
                     "corte": v_cut.get(), "borde": v_border.get()}
            kw = dict(num=num, marks=marks, spine=v_spine.get(),
                      crop_in=float(v_crop_in.get()), crop_out=float(v_crop_out.get()))
            args = (src, dst, v_mode.get(), v_sheet.get(), int(v_dpi.get()),
                    float(v_inset.get()), v_keep.get(), v_gray.get(), 92)
        except (tk.TclError, ValueError):
            if not silent:
                messagebox.showwarning("Malvin", T("msg_numbers"))
            return None
        return args, kw

    def run():
        c = collect()
        if not c:
            return
        args, kw = c
        dst, mode = args[1], args[2]
        W["btn"].configure(state="disabled")
        W["bar"]["value"] = 0

        def work():
            try:
                warn = build(*args, verbose=False, **kw,
                             progress=lambda x: root.after(0, W["bar"].configure, {"value": x}))
                msg = T("msg_done", dst=dst, tip=T(tip_key(mode)))
                if warn:
                    msg += "\n\n" + warn
                root.after(0, done, True, msg)
            except Exception as e:
                root.after(0, done, False, T("err_prefix", e=e))

        threading.Thread(target=work, daemon=True).start()

    # La vista previa se actualiza sola (con una pequena espera) al cambiar cualquier opcion
    for var in (v_in, v_mode, v_spine, v_sheet, v_inset, v_keep, v_gray, v_view, v_crop_in,
                v_crop_out, v_fold, v_fold_where, v_cut, v_border, n_on, n_desde, n_inicio,
                n_hasta, n_tam, n_fuente, n_bold, n_vert, n_horiz, n_mv, n_mh, n_formato):
        var.trace_add("write", schedule_preview)
    for var in (v_in, v_mode):
        var.trace_add("write", refresh_info)

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        v_in.set(sys.argv[1])
        v_out.set(default_out(sys.argv[1]))
    build_ui()
    root.mainloop()


def main():
    set_lang(detect_lang())
    ap = argparse.ArgumentParser(description=f"Malvin v{__version__}: PDF -> booklet / cuadernillo")
    ap.add_argument("pdf", nargs="?", help="PDF de entrada / input PDF")
    ap.add_argument("--version", action="version", version=f"Malvin {__version__}")
    ap.add_argument("-o", "--salida", "--output", help="PDF de salida / output PDF")
    ap.add_argument("-m", "--modo", "--mode", type=alias_mode, choices=MODES, default="sencillo",
                    help="sencillo (1/2) | bolsillo (1/4) | dup2 | dup4 | sin")
    ap.add_argument("--lomo", "--spine", type=alias, choices=SPINES, default="izquierda",
                    help="izquierda | superior | derecha")
    ap.add_argument("-s", "--hoja", "--sheet", choices=list(SHEETS), default="carta")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--margen", "--inset", type=float, default=0.0,
                    help="margen alrededor de cada pagina en mm (0)")
    ap.add_argument("--recorte-interior", "--crop-inner", type=float, default=0.0,
                    help="mm a recortar del margen interior (lado del lomo)")
    ap.add_argument("--recorte-exterior", "--crop-outer", type=float, default=0.0,
                    help="mm a recortar del margen exterior")
    ap.add_argument("--contraportada", "--back-cover", action="store_true",
                    help="la ultima pagina es contraportada: los blancos de relleno van antes "
                         "(por defecto van al final)")
    ap.add_argument("--gris", "--gray", action="store_true", help="escala de grises")
    ap.add_argument("--calidad", "--quality", type=int, default=92, help="calidad JPEG 1-100")
    ap.add_argument("--lang", choices=list(LANGS), help="idioma / language: " + " ".join(LANGS))
    ap.add_argument("--preview-result", action="store_true",
                    help="con --preview: muestra el resultado esperado (ya doblado) en vez de las hojas")
    ap.add_argument("--preview", "--vista-previa", metavar="FILE.png",
                    help="guarda una imagen PNG con la vista previa de las primeras hojas")
    g = ap.add_argument_group("marcas / marks")
    g.add_argument("--pliegue", "--fold", type=alias, choices=STYLE_OPTS, default="ninguna",
                   help="marca de doblez central: ninguna|marcas|linea (none|marks|line)")
    g.add_argument("--pliegue-hojas", "--fold-sheets", type=alias, choices=WHERE_OPTS,
                   default="extremos", help="extremos (primera y ultima hoja) | todas")
    g.add_argument("--corte", "--cut", type=alias, choices=STYLE_OPTS, default="marcas",
                   help="corte (bolsillo, dup2, dup4): ninguna|marcas|linea")
    g.add_argument("--borde", "--page-border", type=alias, choices=BORDER_OPTS, default="ninguna",
                   help="borde de cada pagina original: ninguna|esquinas|contorno")
    g = ap.add_argument_group("numeracion / page numbers")
    g.add_argument("--num", action="store_true", help="numerar paginas / number pages")
    g.add_argument("--num-desde", type=int, default=1, help="pagina del PDF donde empieza (1)")
    g.add_argument("--num-inicio", type=int, default=1, help="numero de esa primera pagina (1)")
    g.add_argument("--num-hasta", type=int, default=0, help="ultima pagina a numerar (0 = final)")
    g.add_argument("--num-tam", type=float, default=12.0, help="tamano en puntos (12)")
    g.add_argument("--num-fuente", default="Arial", help="nombre de fuente o ruta a .ttf")
    g.add_argument("--num-negrita", action="store_true")
    g.add_argument("--num-vert", type=alias, choices=VERT_OPTS, default="inferior")
    g.add_argument("--num-horiz", type=alias, choices=HORIZ_OPTS, default="centro")
    g.add_argument("--num-margen-v", type=float, default=10.0, help="mm al borde superior/inferior (10)")
    g.add_argument("--num-margen-h", type=float, default=15.0, help="mm al borde lateral (15)")
    g.add_argument("--num-formato", default="{n}", help='ej. "- {n} -"')

    cli_flags = any(x.startswith("-") for x in sys.argv[1:])
    if not cli_flags:
        try:
            gui()
            return
        except ImportError:
            pass           # sin tkinter: modo consola
    a = ap.parse_args()
    if a.lang:
        set_lang(a.lang)

    if a.pdf is None:
        path, mode, sheet = interactive()
    else:
        path, mode, sheet = a.pdf, a.modo, a.hoja
    if not os.path.isfile(path):
        sys.exit(f"File not found / No encuentro el archivo: {path}")
    if sheet not in SHEETS:
        sys.exit(f"Sheet? {sheet}")

    num = {"activar": a.num, "desde": a.num_desde, "inicio": a.num_inicio,
           "hasta": a.num_hasta, "tam": a.num_tam, "fuente": a.num_fuente,
           "negrita": a.num_negrita, "vert": a.num_vert, "horiz": a.num_horiz,
           "margen_v": a.num_margen_v, "margen_h": a.num_margen_h, "formato": a.num_formato}
    marks = {"pliegue": a.pliegue, "pliegue_hojas": a.pliegue_hojas, "corte": a.corte,
             "borde": a.borde}
    if a.preview:
        items, _count = make_preview(path, mode, sheet, a.margen, a.contraportada, a.gris,
                                     num=num, marks=marks, spine=a.lomo,
                                     crop_in=a.recorte_interior, crop_out=a.recorte_exterior,
                                     view="result" if a.preview_result else "print")
        preview_png(items, mode in IMPOSED and not a.preview_result, a.preview)
        print(T("log_done", dst=a.preview))
        return
    dst = a.salida or os.path.splitext(path)[0] + f"_malvin_{mode}.pdf"
    build(path, dst, mode, sheet, a.dpi, a.margen, a.contraportada, a.gris, a.calidad,
          num=num, marks=marks, spine=a.lomo, crop_in=a.recorte_interior,
          crop_out=a.recorte_exterior)
    if a.pdf is None:
        input("\nEnter...")


if __name__ == "__main__":
    main()
