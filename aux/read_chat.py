def chatbox_to_txt(data, txt_path):
    f = open(f"{txt_path}", 'a')
    print(data, file=f)
    f.close()