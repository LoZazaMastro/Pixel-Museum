"""Add current onboarding copy without replacing existing interface translations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("it", "es", "fr", "de")
# Each key is the exact English source used by the renderer.
ROWS = [
    ("FILTER", ["FILTRO", "FILTRO", "FILTRE", "FILTER"]),
    ("All exhibits", ["Tutta la collezione", "Toda la colección", "Toute la collection", "Die gesamte Sammlung"]),
    ("Consoles & hardware", ["Console e hardware", "Consolas y hardware", "Consoles et matériel", "Konsolen und Hardware"]),
    ("Games", ["Videogiochi", "Videojuegos", "Jeux", "Spiele"]),
    ("People", ["Persone", "Personas", "Personnalités", "Persönlichkeiten"]),
    ("Culture & industry", ["Cultura e industria", "Cultura e industria", "Culture et industrie", "Kultur und Industrie"]),
    ("Culture & discovery", ["Cultura e scoperte", "Cultura y descubrimientos", "Culture et découvertes", "Kultur und Entdeckungen"]),
    (" (D-pad)", [" (tasti direzionali)", " (cruceta)", " (croix directionnelle)", " (Steuerkreuz)"]),
    (" (Right stick)", [" (levetta destra)", " (stick derecho)", " (stick droit)", " (rechter Stick)"]),
    ("A guide through culture & discovery", ["Una guida tra cultura e scoperte", "Una guía por la cultura y los descubrimientos", "Un guide entre culture et découvertes", "Ein Wegweiser durch Kultur und Entdeckungen"]),
    ("A light space, or a darker room. You can change this later.", ["Uno spazio luminoso o una sala più scura. Puoi cambiare scelta in seguito.", "Un espacio luminoso o una sala más oscura. Puedes cambiarlo después.", "Un espace lumineux ou une salle plus sombre. Vous pourrez changer ce choix plus tard.", "Ein heller Raum oder ein dunklerer Saal. Du kannst diese Wahl später ändern."]),
    ("Two timelines.\nOne world.", ["Due linee del tempo.\nUn solo mondo.", "Dos líneas del tiempo.\nUn mismo mundo.", "Deux chronologies.\nUn même monde.", "Zwei Zeitlinien.\nEine Welt."]),
    ("Look. Listen.\nPlay.", ["Guarda. Ascolta.\nGioca.", "Mira. Escucha.\nJuega.", "Regardez. Écoutez.\nJouez.", "Schauen. Hören.\nSpielen."]),
    ("Your own pace.", ["Al tuo ritmo.", "A tu ritmo.", "À votre rythme.", "In deinem Tempo."]),
    ("Games are more than the things we play. They are people, inventions and places that stay with us. Pixel Museum brings their stories into one collection for you to explore.", [
        "I videogiochi sono più di ciò a cui giochiamo. Sono persone, invenzioni e luoghi che restano con noi. Pixel Museum ne riunisce le storie in una collezione da esplorare.",
        "Los videojuegos son más que aquello a lo que jugamos. Son personas, inventos y lugares que nos acompañan. Pixel Museum reúne sus historias en una colección que puedes explorar.",
        "Les jeux vidéo ne se résument pas à ce à quoi nous jouons. Ce sont aussi des personnes, des inventions et des lieux qui nous accompagnent. Pixel Museum rassemble leurs histoires dans une collection à explorer.",
        "Videospiele sind mehr als das, was wir spielen. Sie sind Menschen, Erfindungen und Orte, die uns begleiten. Pixel Museum vereint ihre Geschichten in einer Sammlung, die du erkunden kannst."
    ]),
    ("The story of play sits beside a wider history of technology, culture and world events. Switching timelines takes you to the closest date, revealing what happened around the same time.", [
        "La storia del videogioco affianca quella più ampia della tecnologia, della cultura e degli eventi del mondo. Passando da una linea del tempo all'altra raggiungi la data più vicina, per scoprire ciò che accadeva nello stesso periodo.",
        "La historia del videojuego convive con una historia más amplia de tecnología, cultura y acontecimientos mundiales. Al cambiar de línea del tiempo llegas a la fecha más cercana y descubres qué ocurría en aquella época.",
        "L'histoire du jeu vidéo côtoie celle, plus vaste, des technologies, de la culture et des événements mondiaux. Passer d'une chronologie à l'autre vous mène à la date la plus proche pour découvrir ce qui se produisait à la même époque.",
        "Die Geschichte der Videospiele steht neben der größeren Geschichte von Technik, Kultur und Weltgeschehen. Beim Wechsel der Zeitlinie gelangst du zum nächstgelegenen Datum und erfährst, was zur selben Zeit geschah."
    ]),
    ("Exhibits unfold through photographs, archive films, music and original interactive experiences. Explore their cards, listen to a score or put an idea into motion. Longer passages can be read in place.", [
        "Le storie prendono forma attraverso fotografie, filmati d'archivio, musica ed esperienze interattive originali. Esplora le schede, ascolta una colonna sonora o metti in movimento un'idea. Puoi scorrere i testi più lunghi senza lasciare la scheda.",
        "Las historias cobran vida con fotografías, películas de archivo, música y experiencias interactivas originales. Explora sus tarjetas, escucha una banda sonora o pon una idea en movimiento. Puedes leer los textos más largos sin salir de la tarjeta.",
        "Les récits se déploient à travers des photographies, des films d'archives, de la musique et des expériences interactives originales. Explorez leurs cartes, écoutez une bande originale ou mettez une idée en mouvement. Les passages plus longs se lisent directement dans leur carte.",
        "Die Ausstellungen erzählen mit Fotografien, Archivfilmen, Musik und eigens gestalteten interaktiven Erlebnissen. Erkunde ihre Karten, höre einen Soundtrack oder setze eine Idee in Bewegung. Längere Texte kannst du direkt in der Karte lesen."
    ]),
    ("Open a photograph to explore its details. Images expand smoothly to fill the screen; move around them or zoom in for a closer look.", [
        "Apri una fotografia per scoprirne i dettagli. Le immagini si espandono fluidamente a schermo intero: spostati al loro interno o ingrandiscile per guardarle da vicino.",
        "Abre una fotografía para explorar sus detalles. Las imágenes se amplían suavemente a pantalla completa: desplázate por ellas o acerca la vista.",
        "Ouvre une photographie pour en explorer les détails. Les images passent en douceur en plein écran : déplace-toi dans leur cadre ou agrandis-les pour les observer.",
        "Öffne ein Foto, um seine Details zu erkunden. Bilder wechseln fließend ins Vollbild: Verschiebe die Ansicht oder zoome für einen genaueren Blick."
    ]),
    ("There is no right order and no need to rush. Colour and music follow each decade. Your guide finds a year or an experience; today's discovery takes you straight to a moment in history.", [
        "Non c'è un ordine da seguire e non c'è fretta. Colori e musica accompagnano ogni decennio. La guida ti porta a un anno o a un'esperienza; la scoperta del giorno ti conduce direttamente a un momento della storia.",
        "No hay un orden correcto ni ninguna prisa. El color y la música acompañan cada década. La guía te lleva a un año o a una experiencia; el descubrimiento del día te conduce directamente a un momento de la historia.",
        "Il n'y a pas d'ordre imposé ni de raison de se presser. Couleurs et musique accompagnent chaque décennie. Le guide vous mène à une année ou à une expérience ; la découverte du jour vous conduit directement à un moment de l'histoire.",
        "Es gibt keine feste Reihenfolge und keinen Grund zur Eile. Farben und Musik begleiten jedes Jahrzehnt. Der Wegweiser führt dich zu einem Jahr oder einem Erlebnis; die Entdeckung des Tages bringt dich direkt zu einem Moment der Geschichte."
    ]),
    ("VIDEO GAMES", ["VIDEOGIOCHI", "VIDEOJUEGOS", "JEUX VIDÉO", "VIDEOSPIELE"]),
    ("CULTURE & DISCOVERY", ["CULTURA E SCOPERTE", "CULTURA Y DESCUBRIMIENTOS", "CULTURE ET DÉCOUVERTES", "KULTUR UND ENTDECKUNGEN"]),
    ("Photographs", ["Fotografie", "Fotografías", "Photographies", "Fotografien"]),
    ("Films", ["Filmati", "Películas", "Films", "Filme"]),
    ("Music", ["Musica", "Música", "Musique", "Musik"]),
    ("History (D-pad up)", ["Storia (tasto direzionale su)", "Historia (cruceta arriba)", "Histoire (croix directionnelle haut)", "Geschichte (Steuerkreuz oben)"]),
    ("Games (D-pad down)", ["Videogiochi (tasto direzionale giù)", "Videojuegos (cruceta abajo)", "Jeux (croix directionnelle bas)", "Spiele (Steuerkreuz unten)"]),
    ("Photo", ["Foto", "Foto", "Photo", "Foto"]),
    ("Guide", ["Guida", "Guía", "Guide", "Wegweiser"]),
    ("Today", ["Oggi", "Hoy", "Aujourd'hui", "Heute"]),
    ("Preferences", ["Preferenze", "Preferencias", "Préférences", "Einstellungen"]),
    ("A PLAYABLE IDEA / PREVIEW", ["UN'IDEA DA GIOCARE / ANTEPRIMA", "UNA IDEA JUGABLE / VISTA PREVIA", "UNE IDÉE À JOUER / APERÇU", "EINE SPIELBARE IDEE / VORSCHAU"]),
]

def main():
    for index, language in enumerate(("en",) + LANGUAGES):
        path = ROOT / "content/ui-locales" / (language + ".json")
        document = json.loads(path.read_text(encoding="utf-8"))
        for source, translations in ROWS:
            assert len(translations) == len(LANGUAGES)
            value = source if index == 0 else translations[index - 1]
            assert value.strip() and len(value.encode("utf-8")) < 8192
            document["strings"][source] = value
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(language, len(document["strings"]), "interface strings")

if __name__ == "__main__":
    main()
