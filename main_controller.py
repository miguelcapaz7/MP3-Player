from song import Song
import vlc
import os
import eyed3
import requests
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from main_window import MainWindow
from rating_window import RatingWindow
from queue_window import ViewQueueWindow
from add_queue_window import AddQueueWindow


class MainController(tk.Frame):
    """
    Controller for our views
    """

    def __init__(self, parent):
        """Creates the main window"""
        tk.Frame.__init__(self, parent)
        self._root_win = tk.Toplevel()
        self._main_window = MainWindow(self._root_win, self)
        self._vlc_instance = vlc.Instance()
        self._player = self._vlc_instance.media_player_new()
        self.list_songs_callback()
        self.queue_titles = []

    def list_songs_callback(self):
        """ Lists song titles in listbox. """
        response = requests.get("http://localhost:5000/songs/all")
        song_list = response.json()
        self.song_title_list = []
        for song in song_list:
            self.song_title_list.append(song['title'])
        self._main_window.add_titles_to_listbox(self.song_title_list)

    def play_callback(self):
        """Play a song specified by the index. """
        index = self._main_window.get_index()
        response = requests.get("http://localhost:5000/songs/all")
        song_list = response.json()
        song = song_list[index]
        media_file = song['pathname'] + song['filename']
        if self._player.get_state() == vlc.State.Playing:
            self._player.stop()
        self.update_play_stats(song['filename'])
        media = self._vlc_instance.media_new_path(media_file)
        self._player.set_media(media)
        self._player.play()
        self._main_window.song_playing['text'] = song['title']
        self._main_window.artist_name['text'] = song['artist']
        self._main_window.runtime_value['text'] = song['runtime']
        self._main_window.album_name['text'] = song['album']
        self._main_window.genre_name['text'] = song['genre']
        self._main_window.state_value['text'] = "Playing"

    def pause_callback(self):
        """ Pause the player """
        if self._player.get_state() == vlc.State.Playing:
            self._player.pause()
            self._main_window.state_value['text'] = "Paused"

    def resume_callback(self):
        """ Resume playing """
        if self._player.get_state() == vlc.State.Paused:
            self._player.pause()
            self._main_window.state_value['text'] = "Playing"

    def stop_callback(self):
        """ Stop the player """
        self._player.stop()
        self._main_window.state_value['text'] = "Stopped"

    def quit_callback(self):
        """ Exit the application. """
        self.master.quit()

    def open_mp3_file(self):
        """ Load the file name selected"""
        abs_path = filedialog.askopenfilename(initialdir='.\\Music\\')
        path = os.getcwd() + "\\Music\\"
        file = os.path.basename(abs_path)
        if file.endswith('.mp3'):
            mp3_file = eyed3.load(os.path.join(path, file))
            runtime = mp3_file.info.time_secs
            mins = int(runtime // 60)
            secs = int(runtime % 60)
            song = Song(str(getattr(mp3_file.tag, 'title')), str(getattr(mp3_file.tag, 'artist')),
                        '{}:{}'.format(mins, secs), '{}'.format(path),
                        '{}'.format(file), str(getattr(mp3_file.tag, 'album')),
                        str(getattr(mp3_file.tag, 'genre')))
            self.add_callback(song)

    def add_callback(self, song):
        """ Add audio file. """
        data = {'title': song.title,
                'artist': song.artist,
                'runtime': song.runtime,
                'pathname': song.pathname,
                'filename': song.filename,
                'album': song.album,
                'genre': song.genre
                }

        response = requests.post("http://localhost:5000/songs", json=data)
        if response.status_code == 200:
            self.list_songs_callback()
            msg_str = song.title + " has been added to library"
            messagebox.showinfo(title="Song Added", message=msg_str)
        else:
            msg_str = response.content
            messagebox.showinfo(title="Error", message=msg_str)

    def update_rating(self, event):
        """Updates the rating for the selected song"""
        index = self._main_window.get_index()
        form_data = self._rate_song.get_form_data()
        try:
            form_data['rating'] = int(form_data['rating'])
            get_response = requests.get("http://localhost:5000/songs/all")
            song_list = get_response.json()
            song = song_list[index]
            response = requests.put("http://localhost:5000/songs/rating/" + song['filename'], json=form_data)
            if response.status_code == 200:
                message = song['title'] + " has been successfully rated"
                messagebox.showinfo(title="Song Rated", message=message)
                self._close_rate_song_popup()
            else:
                message = response.content
                messagebox.showinfo(title="Error", message=message)
        except ValueError:
            message = "Rating must be a number"
            messagebox.showinfo(title="Error", message=message)

    def update_play_stats(self, filename):
        """Updates the play count and last_played"""
        requests.put("http://localhost:5000/songs/play_count/" + filename)

    def delete_callback(self):
        """ Deletes selected song from the library. """
        index = self._main_window.get_index()
        get_response = requests.get("http://localhost:5000/songs/all")
        song_list = get_response.json()
        song = song_list[index]
        filename = song['filename']
        del_response = requests.delete("http://localhost:5000/songs/" + filename)

        if del_response.status_code == 200:
            self.list_songs_callback()
            msg_str = song['title'] + " has been deleted from library"
            messagebox.showinfo(title="Song Added", message=msg_str)
            if song['title'] in self.queue_titles:
                self.queue_titles.remove(song['title'])
        else:
            msg_str = del_response.content
            messagebox.showinfo(title="Song Deleted", message=msg_str)

    def rate_song_popup(self):
        """ Show Rating Popup Window """
        self._rate_win = tk.Toplevel()
        self._rate_song = RatingWindow(self._rate_win, self, self._main_window.get_title())

    def _close_rate_song_popup(self):
        """ Close Rating Popup """
        self._rate_win.destroy()

    def queue_pop_up(self):
        """Loads the Queue Window"""
        self._queue_win = tk.Toplevel()
        self._view_queue = ViewQueueWindow(self._queue_win, self, self.queue_titles)

    def delete_from_queue(self):
        """Removes a song from queue"""
        index = self._view_queue.get_index()
        self.queue_titles.pop(index)
        self._view_queue.list_songs_in_queue()

    def _close_queue_popup(self):
        """ Close Rating Popup """
        self._queue_win.destroy()

    def add_queue_popup(self):
        """Adds the selected song to the queue"""
        self._add_queue_win = tk.Toplevel()
        self._add_queue = AddQueueWindow(self._add_queue_win, self, self.song_title_list)

    def add_to_queue_callback(self):
        """Adds the selected song to the queue list box"""
        index = self._add_queue.get_index()
        get_response = requests.get("http://localhost:5000/songs/all")
        song_list = get_response.json()
        song = song_list[index]
        self._view_queue.listbox.insert(tk.END, song['title'])
        self.queue_titles.append(song['title'])

    def _close_add_queue_popup(self):
        """ Close Rating Popup """
        self._add_queue_win.destroy()


if __name__ == "__main__":
    """ Create Tk window manager and a main window. Start the main loop """
    root = tk.Tk()
    MainController(root).pack()
    tk.mainloop()
