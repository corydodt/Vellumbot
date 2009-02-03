import sys, os

from vellumbot.util.filesystem import Filesystem

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = Filesystem(os.getcwd())
fs.images = fs.new("vellumbot/images", mkdir=1)
fs.party = fs.new("vellumbot/party", mkdir=1)
fs.encounters = fs.new("vellumbot/encounters", mkdir=1)
fs.aliases = fs.new("vellumbot/aliases", mkdir=1)
fs.help = fs("vellumbot/help.txt")
fs.maps = fs.new("vellumbot/maps", mkdir=1)
