import tm_t20 as tm

printer = tm.TMT20(
    senddat="./senddat.exe",
    usb_port="USBPRN",
    keep_script=False,
    )

printer.init()
printer.align("center")
printer.bold(True)

while True:
    while True:
        text = input("text to send, or qr, or cut, or title:")

        match text:
            case "title":
                text = input("text:")
                width = int(input("times width:"))
                height = int(input("times height:"))

                printer.size(width, height)
                printer.line(text)
                printer.size(1, 1)
            case "cut":
                break
            case "qr":
                qrtext = input("qr text or link:")
                qrsize= int(input("qr size min 3 max 12:"))
                printer.qrcode(
                qrtext,
                size=qrsize,
                error_correction="Q")
            case _:
                printer.line(text)

        printer.send()
        printer.clear()
    printer.lf()
    printer.lf()
    printer.lf()
    printer.lf()
    printer.cut(partial=False)

