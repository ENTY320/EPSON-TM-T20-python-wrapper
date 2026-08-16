from math import fabs

import tm_t20 as tm

printer = tm.TMT20(
	senddat="./senddat.exe",
	usb_port="USBPRN")

printer.init()
printer.align("center")
printer.bold(True)




while True:
	while True:
		text = input("text to send or qr or cut:")

		if text == "cut":
			break
		if text == "qr":
			qrtext = input("qr text or link:")
			qrsize= int(input("qr size min 3 max 12:"))
			printer.qrcode(
			qrtext,
			size=qrsize,
			error_correction="Q",)
		else:
			printer.line(text)
		printer.send()
		printer.clear()
	printer.lf()
	printer.lf()
	printer.lf()
	printer.lf()
	printer.cut(partial=False)

