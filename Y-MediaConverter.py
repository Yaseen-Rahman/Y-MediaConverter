from PySide6.QtWidgets import QMainWindow,QTextEdit,QMessageBox,QHBoxLayout,QComboBox,QWidget,QApplication,QVBoxLayout,QLabel,QPushButton,QFileDialog
import sys
from PySide6.QtCore import Qt,QProcess,QThread,Signal
from PySide6.QtGui import QIcon,QColor,QPixmap
import ffmpeg,os
import subprocess,json,time



def relative_path(path):
    if hasattr(sys,"_MEIPASS"):
        return os.path.join(sys._MEIPASS,path)
    return os.path.join(os.path.abspath("."),path)
        
class Probe(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)
    def __init__(self,path,infile):
        super().__init__()
        self.path = path
        self.infile = infile
        

    def run(self):
        cmd = [
            self.path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            self.infile
        ]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW  
            )

            out, err = process.communicate()

            if process.returncode != 0:
                self.error_signal.emit(f"❌ ffprobe error for {self.infile}:\n{err}")
                return None  
            
            self.finished_signal.emit(json.loads(out))
        except Exception as e:
            self.error_signal.emit(f"⚠️ Error occured as: {e}")
            return None




class Media_Converter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Y-MediaConverter(By Y-Softwares)")
        self.setWindowIcon(QIcon("media.ico"))
        self.setGeometry(100,100,550,450)
        self.title = QLabel("Y-MediaConverter",self)
        self.l1 = QLabel("Convert To: ",self)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.showMinimized()
        self.label_i = QLabel(self)
        self.image = QPixmap("vibrant.png")
        self.setMinimumSize(550,450)
        self.setMaximumSize(550,450)
        self.c1 = QComboBox(self)
        self.counter = 0
        self.probe_info = None
        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.chat_end)
        self.select = QPushButton("Browse",self)
        self.trigger = QPushButton("Convert",self)
        self.probe_thread = None
        self.filepath = ""
        self.log = QTextEdit(self)
        self.initUI()


    def initUI(self):
        self.title.setObjectName("title")
        self.l1.setObjectName("l1")
        self.log.setObjectName("log")
        self.label_i.setPixmap(self.image)
        self.label_i.setScaledContents(True)
        self.setObjectName("window")
        self.title.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
        QLabel#title{
        font-size: 30px;
        font-weight: bold;
        font-family: segoe ui;
        }
        QLabel#l1{
        font-size: 25px;
        font-family: segoe ui;
        }
        QTextEdit#log{
        font-size: 16px;
        font-family: times new roman;
        font-weight: 600;
        }
        QPushButton{
        font-size: 17px;
        border: 1px solid;
        background: white;
        border-radius: 4px;
        }
        QComboBox{
        font-size: 18px;
        font-family: helvetica;
        color: black;
        font-weight: bold;
        background: white;
                           }
        QPushButton:hover{
        background: lightblue;
        color: red;                   
        }
        QPushButton:pressed{
        color: darkred;                   
        }
""")
        central = QWidget(self)
        self.log.setReadOnly(True)
        self.setCentralWidget(central)
        vbox = QVBoxLayout()
        vbox.addWidget(self.title)
        hbox =  QHBoxLayout(self)
        widgets = [self.l1,self.c1,self.select,self.trigger]
        for i in widgets:
            hbox.addWidget(i)
        vbox.addLayout(hbox)
        vbox.addWidget(self.label_i)
        vbox.addWidget(self.log)
        self.log.setMinimumHeight(130)
        vfs = [
    "mp4", "mov", "avi", "mkv", "flv", "wmv", "webm", "mpeg", "mpg", "ts", "m4v",
    "3gp", "3g2", "ogv", "asf", "f4v", "vob", "rm", "rmvb", "mts", "m2ts"
]
        self.log.setPlainText("By Y-Softwares!")
        self.c1.addItems(vfs)
        self.trigger.setDisabled(True)
        central.setLayout(vbox)
        self.select.clicked.connect(self.new_process)
        self.trigger.clicked.connect(self.procedure)




    def closeEvent(self,event):
        if not(self.select.isEnabled()):
            reply = QMessageBox.question(self,"Exit?","Are you sure you want to quit during a conversion process?",QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

                                         


    def new_process(self):
        self.log.clear()
        self.filepath,_ = QFileDialog.getOpenFileNames(self,"Select a File/Files","","Video Files(*.mp4 *.avi *.mkv *.mov *.flv *.wmv*.mpeg *.mpg *.webm *.m4v *.3gp *.ts);;All Files(*)","")
        if self.filepath:
            for i,j in enumerate(self.filepath):
                self.log.append(f"{i+1}: {j}")
            self.trigger.setEnabled(True)
        else:
            self.log.setPlainText("Please select a file first!")

            
        

        


    def procedure(self):
        if not self.filepath:
            self.log.setPlainText("Please select a file first!")
            return

        try:
            if self.counter < len(self.filepath):
                ffmpeg_probe = relative_path("ffmpeg/bin/ffprobe.exe")
                in_ext = os.path.splitext(self.filepath[self.counter])[1].lower()
                out_ext = "." + self.c1.currentText()
                
                if in_ext == out_ext:
                    self.log.append(f"⚠️ Skipped: Input and output formats are the same ({in_ext}) for the video {os.path.basename(self.filepath[self.counter])}")
                    return
                
                infile = self.filepath[self.counter]
                self.probe_thread = Probe(ffmpeg_probe,infile)
                self.probe_thread.finished_signal.connect(self.end_probe)
                self.probe_thread.error_signal.connect(self.error_display)
                self.probe_thread.start()
                self.log.setPlainText(f"Please wait while we analyze the video file: {os.path.basename(infile)}")
                self.trigger.setDisabled(True)
                self.select.setDisabled(True)
                self.c1.setDisabled(True)
                base_dir = ""
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(sys.executable)
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))

                folder = os.path.join(base_dir,"Converted")
                os.makedirs(folder,exist_ok=True)
                                

                

        except Exception as e:
            self.log.setPlainText(f"❌ Error: {e}")

            
    def end_probe(self,info):
        codec_com = {
        ".mp4": {"video": ("h264", "hevc"), "audio": ("aac", "mp3")},
        ".mkv": {"video": ("h264", "hevc", "vp9", "av1"), "audio": ("aac", "mp3", "opus", "vorbis", "flac")},
        ".avi": {"video": ("mpeg4", "h264"), "audio": ("mp3", "pcm_s16le")},
        ".mov": {"video": ("h264", "prores", "hevc"), "audio": ("aac", "pcm_s16le", "alac")},
        ".flv": {"video": ("flv1", "h264"), "audio": ("mp3", "aac")},
        ".ts": {"video": ("h264", "hevc", "mpeg2video"), "audio": ("aac", "mp2", "ac3")},
        ".webm": {"video": ("vp8", "vp9", "av1"), "audio": ("opus", "vorbis")},
        ".wmv": {"video": ("wmv1", "wmv2", "wmv3"), "audio": ("wmav1", "wmav2")}
        }

        if not info:
            self.error_display("Error in probing the video!")
            return 

        v_codec, a_codec = None, None
        self.log.append(f"Probing of video completed!")
        for stream in info["streams"]:
            if stream["codec_type"] == "video" and not v_codec:
                v_codec = stream["codec_name"]
            elif stream["codec_type"] == "audio" and not a_codec:
                a_codec = stream["codec_name"]
        infile = self.filepath[self.counter]
        _ , ext = os.path.splitext(infile)

        
        if ext in codec_com:
            comp = codec_com[ext]
            if v_codec in comp["video"] and a_codec in comp["audio"]:
                vcodec, acodec = "copy", "copy"
            else:
                if ext in [".mp4", ".mkv"]:
                    vcodec, acodec = "libx264", "aac"
                elif ext == ".avi":
                    vcodec, acodec = "mpeg4", "mp3"
                elif ext == ".mov":
                    vcodec, acodec = "libx264", "aac"
                elif ext == ".flv":
                    vcodec, acodec = "flv", "aac"
                elif ext == ".ts":
                    vcodec, acodec = "libx264", "aac"
                elif ext == ".webm":
                    vcodec, acodec = "libvpx-vp9", "opus"
                elif ext == ".wmv":
                    vcodec, acodec = "wmv2", "wmav2"
        
        else:
            self.log.setPlainText(f"{infile}: Unknown container — using default H.264/AAC.")
            vcodec, acodec = "libx264", "aac"

        self.ffmpeg_process(vcodec,acodec)


    def ffmpeg_process(self,vcodec,acodec):
        try:
            ffmpeg_path = relative_path("ffmpeg/bin/ffmpeg.exe")
            infile = self.filepath[self.counter]
            output_file, _ = os.path.splitext(infile)
            base_dir = ""
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            output = os.path.join(
                    base_dir,
                    "Converted",
                    f"{os.path.basename(output_file)}_converted.{self.c1.currentText()}"
                    )
            if os.path.exists(output):
                time_now = time.strftime("%M-%S")
                output = os.path.join(
                    base_dir,
                    "Converted",
                    f"{os.path.basename(output_file)}_converted({time_now}).{self.c1.currentText()}")
                     
            outdir = os.path.dirname(output)
            os.makedirs(outdir, exist_ok=True)

            cmd = [
                        "ffmpeg",
                        "-i", infile,
                        "-c:v", vcodec,
                        "-c:a", acodec,
                        "-y", output
                    ]
            if vcodec != "copy":
                cmd += ["-crf", "23", "-preset", "fast"]


                                
            self.log.setPlainText(f"🔄 Conversion started for {os.path.basename(infile)}...\n")
            self.process.start(ffmpeg_path, cmd[1:])

        except Exception as e:
            self.log.append(f"Error identified: {e}")
                





    def error_display(self,message):
        self.log.append(f"Error occured as {message}!")




    def read_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log.append(data)

    def chat_end(self):
        self.counter += 1
        if self.counter < len(self.filepath):
            self.procedure()
        else:
            self.select.setDisabled(False)
            self.c1.setDisabled(False)
            self.counter = 0
            for i in self.filepath:
                self.log.append(f"\n✅ Conversion finished for {os.path.basename(i)}!")
            self.log.append("🎉 All conversions done!")
            QMessageBox.information(self, "Done", "All conversions completed successfully.")



def main():
    app = QApplication(sys.argv)
    window = Media_Converter()
    window.show()
    app.exit(app.exec_())


if __name__ == "__main__":
    main()

