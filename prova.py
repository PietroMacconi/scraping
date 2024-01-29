
class YT_link_converter():
    def __init__(self, link):
        self.link = link
    def convert_YT_link(self,link):
        link = link.replace('/', '-')
        link = link.replace('?', '_')
        link = link.replace('=', ',')
        return link
    def convert_original_YT_link (self, link):
        link = link.replace('-','/')
        link = link.replace('_', '?')
        link = link.replace(',', '=')
        return link

    def obtain_link_from_file (self, link):
        link = link.replace('-dataframe-','')
        link = self.convert_original_YT_link(link)
        return link

