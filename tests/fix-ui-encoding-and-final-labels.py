"""UTF-8 repair of all new phase/decade labels and startup/provider errors."""
from pathlib import Path
import json

keys = ['Checking for updates...', 'Up to date', 'Available', 'Downloading...', 'Ready', 'Could not check', 'Updates are available.', 'Your update is ready.', 'The check could not be completed.', 'Looking for app and database updates.', 'You can continue exploring while the updates are prepared.', 'Download the available updates for Pixel Museum.', 'Restart Pixel Museum to finish installing the update.', 'Open Pixel Museum again to use the new database.', 'Please try again later.', 'You already have the latest app and database.', 'Database']
values = {
    'it': ['Controllo degli aggiornamenti...', 'Aggiornato', 'Disponibile', 'Download in corso...', 'Pronto', 'Controllo non riuscito', 'Sono disponibili aggiornamenti.', 'Il tuo aggiornamento è pronto.', 'Non è stato possibile completare il controllo.', 'Ricerca di aggiornamenti per l’app e il database.', 'Puoi continuare a esplorare mentre gli aggiornamenti vengono preparati.', 'Scarica gli aggiornamenti disponibili per Pixel Museum.', 'Riavvia Pixel Museum per completare l’installazione dell’aggiornamento.', 'Apri di nuovo Pixel Museum per usare il nuovo database.', 'Riprova più tardi.', 'Hai già l’ultima versione dell’app e del database.', 'Database'],
    'es': ['Buscando actualizaciones...', 'Actualizado', 'Disponible', 'Descargando...', 'Listo', 'No se pudo comprobar', 'Hay actualizaciones disponibles.', 'Tu actualización está lista.', 'No se pudo completar la comprobación.', 'Buscando actualizaciones de la app y la base de datos.', 'Puedes seguir explorando mientras se preparan las actualizaciones.', 'Descarga las actualizaciones disponibles para Pixel Museum.', 'Reinicia Pixel Museum para terminar de instalar la actualización.', 'Vuelve a abrir Pixel Museum para usar la nueva base de datos.', 'Vuelve a intentarlo más tarde.', 'Ya tienes la última versión de la app y la base de datos.', 'Base de datos'],
    'fr': ['Recherche de mises à jour...', 'À jour', 'Disponible', 'Téléchargement...', 'Prêt', 'Vérification impossible', 'Des mises à jour sont disponibles.', 'Votre mise à jour est prête.', 'La vérification n’a pas pu être terminée.', 'Recherche de mises à jour de l’application et de la base de données.', 'Vous pouvez continuer votre visite pendant la préparation des mises à jour.', 'Téléchargez les mises à jour disponibles pour Pixel Museum.', 'Redémarrez Pixel Museum pour terminer l’installation de la mise à jour.', 'Rouvrez Pixel Museum pour utiliser la nouvelle base de données.', 'Veuillez réessayer plus tard.', 'Vous disposez déjà des dernières versions de l’application et de la base de données.', 'Base de données'],
    'de': ['Suche nach Updates...', 'Aktuell', 'Verfügbar', 'Wird heruntergeladen...', 'Bereit', 'Prüfung fehlgeschlagen', 'Updates sind verfügbar.', 'Dein Update ist bereit.', 'Die Prüfung konnte nicht abgeschlossen werden.', 'Es wird nach Updates für App und Datenbank gesucht.', 'Du kannst das Museum weiter erkunden, während die Updates vorbereitet werden.', 'Lade die verfügbaren Updates für Pixel Museum herunter.', 'Starte Pixel Museum neu, um die Installation des Updates abzuschließen.', 'Öffne Pixel Museum erneut, um die neue Datenbank zu verwenden.', 'Bitte versuche es später erneut.', 'Du hast bereits die neueste Version der App und der Datenbank.', 'Datenbank'],
}
extra = {
    'Previous decade': ['Decennio precedente', 'Década anterior', 'Décennie précédente', 'Vorheriges Jahrzehnt'],
    'Next decade': ['Decennio successivo', 'Década siguiente', 'Décennie suivante', 'Nächstes Jahrzehnt'],
    'Check for updates': ['Controlla aggiornamenti', 'Buscar actualizaciones', 'Rechercher des mises à jour', 'Nach Updates suchen'],
    "Pixel Museum's resources were not found. Please run the setup and choose the Pixel Museum installation folder.": ['Le risorse di Pixel Museum non sono state trovate. Avvia il programma di installazione e scegli la cartella di installazione di Pixel Museum.', 'No se han encontrado los recursos de Pixel Museum. Ejecuta el instalador y elige la carpeta de instalación de Pixel Museum.', 'Les ressources de Pixel Museum sont introuvables. Lancez le programme d’installation et choisissez le dossier d’installation de Pixel Museum.', 'Die Ressourcen von Pixel Museum wurden nicht gefunden. Starte das Installationsprogramm und wähle den Installationsordner von Pixel Museum.'],
    'The museum could not initialize. See session-windows.log in the installation folder.': ['Impossibile avviare il museo. Consulta session-windows.log nella cartella di installazione.', 'No se ha podido iniciar el museo. Consulta session-windows.log en la carpeta de instalación.', 'Le musée n’a pas pu démarrer. Consultez session-windows.log dans le dossier d’installation.', 'Das Museum konnte nicht gestartet werden. Sieh in session-windows.log im Installationsordner nach.'],
    'Could not connect to YouTube. Please try again.': ['Impossibile connettersi a YouTube. Riprova.', 'No se ha podido conectar con YouTube. Vuelve a intentarlo.', 'Impossible de se connecter à YouTube. Veuillez réessayer.', 'Die Verbindung zu YouTube konnte nicht hergestellt werden. Bitte versuche es erneut.'],
    'Remove the images saved on this console?': ['Rimuovere le immagini salvate su questa console?', '¿Eliminar las imágenes guardadas en esta consola?', 'Supprimer les images enregistrées sur cette console ?', 'Die auf dieser Konsole gespeicherten Bilder löschen?'],
}
locales = ['it', 'es', 'fr', 'de']
for locale in ['en'] + locales:
    path = Path('content/ui-locales') / (locale + '.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    data['strings'].update(zip(keys, keys if locale == 'en' else values[locale]))
    for key, translations in extra.items():
        data['strings'][key] = key if locale == 'en' else translations[locales.index(locale)]
    if locale == 'es':
        data['strings']['LINES'] = 'LÍNEAS'
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('UTF-8 fixes and all three final error keys written in five locales.')
