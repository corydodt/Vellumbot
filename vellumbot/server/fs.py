import sys, os

from vellumbot.util.filesystem import Filesystem

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = Filesystem(os.getcwd())
fs.aliases = fs.new("vellumbot/aliases", mkdir=1)
fs.hypy = fs.new('vellumbot/srd35-index', mkdir=1)
fs.help = fs("vellumbot/help.txt")
fs.userdb = fs('vellumbot/user.db')

