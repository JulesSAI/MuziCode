import re
from pydub import AudioSegment
from pydub.playback import play, _play_with_simpleaudio
from typing import Dict, List, Optional
import os


class MusicSequencer:
    def __init__(self):
        self.tempo: int = 120
        self.patterns: Dict[str, List[int]] = {}
        self.melodies: Dict[str, List[str]] = {}
        self.samples_dir: str = "samples"
        self.notes_dir: str = "notes"
        self.current_playback = None

    def stop_playback(self) -> None:
        """Detiene la reproducción actual"""
        if self.current_playback:
            self.current_playback.stop()

    def parse_line(self, line: str) -> None:
        """Parse a line from the song file, handling comments and commands."""
        line = line.split('#')[0].strip()  # Remove comments
        if not line:
            return

        if m := re.match(r'tempo\s+(\d+)', line, re.IGNORECASE):
            self.set_tempo(int(m.group(1)))
        elif m := re.match(r'pattern\s+(\w+)\s*=\s*\[(.*)\]', line, re.IGNORECASE):
            name = m.group(1)
            vals = list(map(int, [x.strip() for x in m.group(2).split(',') if x.strip()]))
            self.patterns[name] = vals
        elif m := re.match(r'melody\s+(\w+)\s*=\s*\[(.*)\]', line, re.IGNORECASE):
            name = m.group(1)
            notes = [n.strip() for n in m.group(2).split(',') if n.strip()]
            self.melodies[name] = notes
        elif m := re.match(r'mix\s*\((.*)\)', line, re.IGNORECASE):
            items = [x.strip() for x in m.group(1).split(',') if x.strip()]
            self.mix_and_play(items)
        elif m := re.match(r'save\s+(\S+)', line, re.IGNORECASE):
            filename = m.group(1)
            items = [x.strip() for x in line.split('(')[1].split(')')[0].split(',') if x.strip()]
            self.mix_and_save(items, filename)

    def set_tempo(self, new_tempo: int) -> None:
        """Establece el tempo con validación"""
        if 20 <= new_tempo <= 300:
            self.tempo = new_tempo
        else:
            print(f"Tempo {new_tempo} fuera de rango (20-300). Usando valor por defecto 120.")

    def load_audio_file(self, file_path: str) -> Optional[AudioSegment]:
        """Carga un archivo de audio con manejo de errores"""
        try:
            if not os.path.exists(file_path):
                print(f"Archivo no encontrado: {file_path}")
                return None
            return AudioSegment.from_wav(file_path)
        except Exception as e:
            print(f"Error cargando {file_path}: {str(e)}")
            return None

    def mix_and_play(self, items: List[str], loop: bool = False) -> None:
        """Mezcla y reproduce los patrones/melodías"""
        if not items:
            print("Error: No hay items para mezclar")
            return

        beat_ms = 60000 // self.tempo
        final = AudioSegment.silent(duration=beat_ms * 4)  # Compás de 4 tiempos

        for name in items:
            sound = None

            if name in self.patterns:
                sound = self.create_pattern_sound(name, beat_ms)
            elif name in self.melodies:
                sound = self.create_melody_sound(name, beat_ms)

            if sound:
                final = final.overlay(sound)

        self.stop_playback()
        self.current_playback = _play_with_simpleaudio(final)
        if loop:
            # Implementar lógica de loop aquí
            pass

    def mix_and_save(self, items: List[str], filename: str) -> None:
        """Mezcla y guarda a un archivo"""
        beat_ms = 60000 // self.tempo
        final = AudioSegment.silent(duration=beat_ms * 4)

        for name in items:
            sound = None

            if name in self.patterns:
                sound = self.create_pattern_sound(name, beat_ms)
            elif name in self.melodies:
                sound = self.create_melody_sound(name, beat_ms)

            if sound:
                final = final.overlay(sound)

        final.export(filename, format="wav")
        print(f"Mezcla guardada como {filename}")

    def create_pattern_sound(self, name: str, beat_ms: int) -> Optional[AudioSegment]:
        """Crea un AudioSegment para un patrón rítmico"""
        sound = AudioSegment.silent(duration=0)
        pattern = self.patterns[name]

        hit_sound = self.load_audio_file(f"{self.samples_dir}/{name}.wav")
        if not hit_sound:
            return None

        for val in pattern:
            if val == 1:
                sound += hit_sound + AudioSegment.silent(duration=beat_ms - len(hit_sound))
            else:
                sound += AudioSegment.silent(duration=beat_ms)

        return sound

    def create_melody_sound(self, name: str, beat_ms: int) -> Optional[AudioSegment]:
        """Crea un AudioSegment para una melodía"""
        sound = AudioSegment.silent(duration=0)

        for note in self.melodies[name]:
            note_audio = self.load_audio_file(f"{self.notes_dir}/{note}.wav")
            if note_audio:
                sound += note_audio + AudioSegment.silent(duration=beat_ms - len(note_audio))
            else:
                sound += AudioSegment.silent(duration=beat_ms)

        return sound

    def load_song_file(self, filename: str) -> None:
        """Carga y ejecuta un archivo de canción"""
        try:
            with open(filename, "r") as file:
                for line in file:
                    self.parse_line(line.strip())
        except FileNotFoundError:
            print(f"Error: Archivo {filename} no encontrado")
        except Exception as e:
            print(f"Error procesando archivo: {str(e)}")


# Ejemplo de uso
if __name__ == "__main__":
    sequencer = MusicSequencer()

    # Configurar rutas personalizadas (opcional)
    # sequencer.samples_dir = "my_samples"
    # sequencer.notes_dir = "my_notes"

    # Cargar y ejecutar el archivo de canción
    sequencer.load_song_file("song.loop")

    # Ejemplo de cómo mezclar directamente desde código
    # sequencer.parse_line("pattern drums = [1,0,1,0]")
    # sequencer.parse_line("melody lead = [C4,D4,E4,F4]")
    # sequencer.parse_line("mix(drums, lead)")