"""Use UTF-8 source text explicitly; repair the tokenized workshop help entry."""
from pathlib import Path
import json
import re

key = 'Start with a white 16-by-16 canvas. Choose a pixel, draw with the selected colour, or erase it to white. Hold {l1}/{r1} to browse the NES-inspired palette; sixteen colours are visible at once. White is available only through the eraser. {triangle} clears the canvas. The {touchpad} is not used.'
translations = {
    'en': key,
    'it': 'Inizia con una tela bianca di 16×16 pixel. Scegli un pixel, disegna con il colore selezionato o cancellalo per riportarlo al bianco. Tieni premuti {l1}/{r1} per scorrere la tavolozza ispirata al NES: sedici colori sono visibili alla volta. Il bianco si ottiene solo con la gomma. {triangle} svuota la tela. Il {touchpad} non viene usato.',
    'es': 'Empieza con un lienzo blanco de 16×16 píxeles. Elige un píxel, dibuja con el color seleccionado o bórralo para devolverlo al blanco. Mantén {l1}/{r1} para recorrer la paleta inspirada en NES: se ven dieciséis colores a la vez. El blanco solo se obtiene con la goma. {triangle} vacía el lienzo. No se utiliza el {touchpad}.',
    'fr': 'Commencez avec une toile blanche de 16×16 pixels. Choisissez un pixel, dessinez avec la couleur sélectionnée ou effacez-le pour le remettre en blanc. Maintenez {l1}/{r1} pour parcourir la palette inspirée de la NES : seize couleurs sont visibles à la fois. Utilisez la gomme pour retrouver le blanc. {triangle} efface la toile. Le {touchpad} n’est pas utilisé.',
    'de': 'Beginne mit einer weißen Fläche aus 16×16 Pixeln. Wähle einen Pixel, zeichne mit der ausgewählten Farbe oder radiere ihn wieder weiß. Halte {l1}/{r1}, um die vom NES inspirierte Palette zu durchblättern: Jeweils sechzehn Farben sind sichtbar. Weiß erhältst du nur mit dem Radierer. {triangle} leert die Fläche. Das {touchpad} wird nicht verwendet.',
}
for locale, value in translations.items():
    path = Path('content/ui-locales') / (locale + '.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    for entry, text in data['strings'].items():
        data['strings'][entry] = re.sub(r'\{\{(left_stick|right_stick|dpad|touchpad|cross|circle|square|triangle|l1|r1|l2|r2|options)\}\}', r'{\1}', text)
    data['strings'][key] = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Repaired all workshop controller tokens in five locales.')
