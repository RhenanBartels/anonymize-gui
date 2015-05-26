#!/usr/bin/env/ python
#_*_coding: utf-8 _*_

import datetime
import dicom
import glob
import hashlib
import os
import pdb
import sys
import time
import Tkinter

import tkFileDialog
import tkMessageBox


#TODO: NOT CREATING A FILE FOR EACH PATIENT. _list_dicom logi.
reload(sys)
sys.setdefaultencoding('utf-8')

#Fields that will be removed
FIELDS = [(0x10, 0x10), (0x08, 0x20), (0x08, 0x80), (0x08, 0x81),
        (0x08, 0x23), (0x08, 0x90), (0x08,0x1010), (0x10, 0x20), (0x20, 0x10)]

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
        self.window.resizable(0, 0)

        folder_label = Tkinter.Label(self.window, text="Folder:")
        self.string_entry = Tkinter.StringVar()
        self.folder_entry = Tkinter.Entry(self.window,
                textvariable=self.string_entry, width=45)
        self.verbose_string = Tkinter.StringVar()
        self.verbose_label = Tkinter.Label(text="",
                textvar=self.verbose_string)
        self.check_box_val = Tkinter.IntVar()
        self.check_box = Tkinter.Checkbutton(self.window,
                text='Save all patients in the same folder',
                variable=self.check_box_val)
        load_button = Tkinter.Button(self.window, text="Load",
                command=self.load_callback, width=10)
        self.run_button = Tkinter.Button(self.window, text="Run",
                width=10, state=Tkinter.DISABLED, command=self.run_callback)

        #set the position of the button
        folder_label.grid(row=0, column=0)
        self.folder_entry.grid(row=0, column=1)
        #self.verbose_label.grid(row=1, column=1)
        self.check_box.grid(row=2, column=1, columnspan=1)
        load_button.grid(row=3, column=1, columnspan=1, padx=0)
        self.run_button.grid(row=4, column=1, padx=0)


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
        #Walk through the directory tree
        fields_folder = self._create_fields_folder()
        common_folder = self._create_images_folder()
        created_folders = [os.path.join(self.file_path, x) for x in
                ["AnonymizedDicomFiles", "AnonymizedFieldsInformation"]]

        for current_folder, dirs, files in os.walk(self.file_path):
            parent_folder = self._get_parent_folder(current_folder)
            if parent_folder == self.file_path and current_folder not in\
                    created_folders:
                seed = str(datetime.datetime.now())
                save_folder = os.path.join(common_folder,
                        self._create_folder_name(seed))
                self._create_folder(save_folder)
                self._create_patient_file(fields_folder, current_folder,
                            seed)
            if save_folder in locals():
                for name in files:
                    if name.endswith(".dcm"):
                        dicom_path = os.path.join(current_folder, name)
                        if not os.path.exists(os.path.join(
                            save_folder, name)):
                            self._anonymize_dicom(dicom_path, save_folder)

        tkMessageBox.showinfo("Say Hello", "Hello World")

    def _check_directory(self, path):
        """
            Check if the Anonymized directory already exists
        """
        if os.path.isdir(path):
           self.log("Directory Already Exists!")
           return False
        return True

    def _create_fields_folder(self):
        folder_name = os.path.join(self.file_path,
                "AnonymizedFieldsInformation")
        self._create_folder(folder_name)
        return folder_name

    def _is_same_folder(self):
        checkbox_state = self.check_box_val.get()
        return checkbox_state

    def _create_images_folder(self):
        folder_name = os.path.join(self.file_path,
                "AnonymizedDicomFiles")
        self._create_folder(folder_name)
        return folder_name

    def _create_folder_name(self, seed):
        date = datetime.datetime.now()
        folder_name =''.join(map(str, [date.year, date.month, date.day])) + \
                 "_" + hashlib.sha224(seed).hexdigest()[0:10]
        return folder_name

    def _get_parent_folder(self, path):
        """
           Return the path of the parent folder of the current one
        """
        parent_folder = path.split(os.sep)
        parent_folder.pop(-1)
        return (os.sep).join(parent_folder)

    def _anonymize_dicom(self, path, save_folder):
        """
            Run over all dicom files of the current folder
            and replace some fields by **********
        """
        dicom_obj = dicom.read_file(path)
        try:
            slice_position = str(dicom_obj[0x20, 0x1041].value)
        except:
            pass
        for field in FIELDS:
            dicom_obj[field].value = "**********"

        output_path = os.path.join(save_folder, slice_position + ".dcm")
        dicom_obj.save_as(output_path)

    def _get_dicom_info(self, dicom_obj, new_id):
        dicom_info = {}
        dicom_info['New ID'] = new_id
        for field in FIELDS:
            try:
                dicom_info[dicom_obj[field].name] = dicom_obj[field].value
            except:
                pass
        return dicom_info

    def _create_patient_file(self, path, current_folder,
            seed):
        file_extension = os.path.join(current_folder, "*.dcm")
        dicom_files = glob.glob(file_extension)
        if dicom_files:
            dicom_obj = dicom.read_file(dicom_files[0])
            new_id = self._create_folder_name(seed)
            save_path = os.path.join(path, new_id + ".txt")
            dicom_info = self._get_dicom_info(dicom_obj, new_id)
            if not os.path.exists(save_path):
                with open(save_path, 'a') as fobj:
                    for key, value in dicom_info.items():
                        fobj.write(key + " - " + value + "\n")

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
        self.window.geometry('{}x{}+{}+{}'.format(440, 100, x, y))


    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = Gui()
    app.run()


