#!/usr/bin/env/ python
#_*_coding: utf-8 _*_

import dicom
import glob
import os
import pdb
import time
import Tkinter

import tkFileDialog

FIELDS = [(0x10, 0x10)]

class Gui(object):
    """
        Main class of the anonymizegui.py program
    """
    def __init__(self):
        """
            Create the main window and adds the widgets.
        """
        self.window = Tkinter.Tk()
        self.window.title("Anonymize Tool")
        #self.window.geometry("500x120")
        self._center_screen()

        folder_label = Tkinter.Label(self.window, text="Folder")
        self.string_entry = Tkinter.StringVar()
        self.folder_entry = Tkinter.Entry(self.window,
                textvariable=self.string_entry, width=80)
        self.verbose_string = Tkinter.StringVar()
        self.verbose_label = Tkinter.Label(text="",
                textvar=self.verbose_string)
        load_button = Tkinter.Button(self.window, text="Load",
                command=self.load_callback, width=10)
        self.run_button = Tkinter.Button(self.window, text="Run",
                width=10, state=Tkinter.DISABLED, command=self.run_callback)

        #set the position of the button
        folder_label.grid(row=0, column=0)
        self.folder_entry.grid(row=0, column=1)
        self.verbose_label.grid(row=1, column=1)
        load_button.grid(row=2, column=0)
        self.run_button.grid(row=2, column=1)

        folder_label.pack()
        self.folder_entry.pack()
        self.verbose_label.pack()
        load_button.pack()
        self.run_button.pack()

    def load_callback(self):
        """
            Callback of the 'load' button.

            Opens a dialog box which allows the user to select a folder.
        """
        self.file_path = tkFileDialog.askdirectory(title="Choose the Folder")
        if self.file_path:
            self.string_entry.set(self.file_path)
            self.run_button.config(state=Tkinter.NORMAL)

    def run_callback(self):
        """
            Callback of the 'run' button.

            Run over all directory tree and anonymized all dicom files inside.
            In the end all anonymized files will be stored in a respective
            folded called Anoymized.

        """
        if hasattr(self, 'file_path'):
            self.log("Anonymizing...")
            #Walk through the directory tree
            for root, dirs, files in os.walk(self.file_path):
                current_folder = root
                if self._list_dicom(current_folder):
                    parent_folder = self._get_parent_folder(current_folder)
                    if parent_folder == self.file_path:
                        save_folder = os.path.join(current_folder,
                                "Anonymized")
                    else:
                        save_folder = os.path.join(parent_folder,
                                "Anonymized")
                    self._create_folder(save_folder)

                    for name in files:
                        if name.endswith(".dcm"):
                            dicom_path = os.path.join(root, name)
                            output_path = os.path.join(save_folder, name)
                            self._anonymize_dicom(dicom_path, output_path)

            self.log("Done!")

    def log(self, msg):
        self.verbose_string.set(msg)

    def _check_directory(self, path):
        """
            Check if the Anonymized directory already exists
        """
        if os.path.isdir(path):
           self.log("Directory Already Exists!")
           return False
        return True

    def _get_patient_name(self, dicom_obj):
        """
            Return the patient name to write on on text file
        """
        patient_name = dicom.obj[0x10, 0x10].value
        return patient_name

    def _get_parent_folder(self, path):
        """
           Return the path of the parent folder of the current one
        """
        parent_folder = path.split(os.sep)
        parent_folder.pop(-1)
        return (os.sep).join(parent_folder)

    def _anonymize_dicom(self, path, output_path):
        """
            Run over all dicom files of the current folder
            and replace some fields by **********
        """
        dicom_obj = dicom.read_file(path)
        for field in FIELDS:
            dicom_obj[field].value = "**********"
        dicom_obj.save_as(output_path)

    def _create_patient_file(self, path):
        pass

    def _list_dicom(self, path):
        """
            Check if the current folder have dicom files
        """
        if glob.glob(os.path.join(path,"*.dcm")):
            return True
        return False

    def _create_folder(self, path):
        try:
            os.mkdir(path)
        except:
            pass

    def _center_screen(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry('{}x{}+{}+{}'.format(500, 120, x, y))


    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = Gui()
    app.run()


