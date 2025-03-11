import os
import smtplib
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

#A simple Python script that sends the selected EPUB files to a designated
#basename = os.path.basename(selected_file)

class Send2Kindle:
    def __init__(self):
        # SMTP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWD and 
        # KINDLE_EMAIL_ADDRESS need to be filled out before deployment.
        self.kindle_email = os.getenv('KINDLE_EMAIL_ADDRESS')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWD')
        pass

    def send(self):
        smtp_obj = smtplib.SMTP(self.smtp_server, 587)
        smtp_obj.starttls()
        smtp_obj.login(self.email_address, self.password)
        to_addr = self.kindle_email

        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, 'utf-8').encode(), addr))

        msg = MIMEMultipart()
        msg['From'] = _format_addr(smtp_obj.user)
        msg['To'] = _format_addr(to_addr)
        msg['Subject'] = Header('Sent to Kindle', 'utf-8').encode()
        msg.attach(
            MIMEText('A Voyage to Kindle Powered by Python.', 'plain', 'utf-8'))
        with open(  sys.argv[1], 'rb') as f:
            mime = MIMEBase('document', 'mobi', filename=basename)
            mime.add_header('Content-Disposition',
                            'attachment', filename=basename)
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            mime.set_payload(f.read())
            encoders.encode_base64(mime)
            msg.attach(mime)

        smtp_obj.sendmail(smtp_obj.user, to_addr, msg.as_string())
