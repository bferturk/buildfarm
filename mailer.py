#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 TUBITAK/UEKAE
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Please read the COPYING file.

""" Standart Python Modules """
import os
import sys
import socket
import smtplib

import pisi.specfile

""" BuildFarm Modules """
import config
import logger
import templates as tmpl

try:
    import mailauth
except ImportError:
    print "You have to create a mailauth.py file for defining 'username' and 'password'."
    sys.exit(1)

class MailerError(Exception):
    pass


def send(message, pspec = "", type = ""):

    def wrap(message, length=72):
        return reduce(lambda line, word: "%s%s%s" %
                      (line,
                       [" ", "\n"][(len(line)-line.rfind("\n")-1 + len(word.split("\n",1)[0]) >= length)],
                       word),
                      message.split(" "))

    if not config.useSmtpAuth and (not mailauth.username or not mailauth.password):
        logger.info("Herhangi bir SMTP kullanıcı ve parolası çifti tanımlanmadığı için e-posta gönderilmiyor.")
        return

    recipientsName, recipientsEmail = [], []
    if pspec:
        specFile = pisi.specfile.SpecFile()
        specFile.read(os.path.join(config.localPspecRepo, pspec))
        recipientsName.append(specFile.source.packager.name)
        recipientsEmail.append(specFile.source.packager.email)

    templates = {"error": tmpl.error_message,
                 "info" : tmpl.info_message,
                 "announce" : tmpl.announce_message}

    packagename=os.path.basename(os.path.dirname(pspec))
    last_log = "".join(open(config.logFile).readlines()[-20:]) # FIXME: woohooo, what's this ;)
    message = templates.get(type) % {'log'      : wrap(last_log),
                                 'recipientName': ' ve '.join(recipientsName),
                                 'mailTo'       : ', '.join(recipientsEmail),
                                 'ccList'       : ', '.join(config.ccList),
                                 'mailFrom'     : config.mailFrom,
                                 'announceAddr' : config.announceAddr,
                                 'subject'      : pspec or type,
                                 'message'      : wrap(message),
                                 'pspec'        : pspec,
                                 'type'         : type,
                                 'packagename'  : packagename}

    # timeout value in seconds
    socket.setdefaulttimeout(10)

    try:
        session = smtplib.SMTP(config.smtpServer)
    except:
        logger.error("E-posta gönderimi gerçekleştirilemedi: Sunucuda oturum açılamadı (%s)." % config.smtpServer)
        return

    if config.useSmtpAuth and mailauth.password:
        try:
            session.login(mailauth.username, mailauth.password)
        except smtplib.SMTPAuthenticationError:
            logger.error("E-posta gönderimi gerçekleştirilemedi: Kimlik doğrulama başarısız.")
            return

    if type == "announce":
        smtpresult = session.sendmail(config.mailFrom, config.announceAddr , message)
    else:
        smtpresult = session.sendmail(config.mailFrom, recipientsEmail + config.ccList, message)

def error(message, pspec):
    send(message, pspec, type = "error")

def info(message):
    send(message, type = "info")

def announce(message):
    send(message, type = "announce")
