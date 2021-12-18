import validators
from html2image import Html2Image
from urllib.parse import urlparse
from PIL import Image
from .LinkPreview import linkPreview

# Html2Image object used to convert HTML code into a .png file. Does so by taking a screenshot of the HTML output.
hti = Html2Image()
# Designated output path for the screenshots to be stored in. All screenshots are kept inside the 'images' folder.
hti.output_path = 'images'

# HTML template for the link preview.
linkPreviewTemplate = r'''
<div class="div-link-preview">
    <div class="div-link-preview-col div-link-preview-col-l">
        <img class="div-link-preview-img" src="{img_link:}">
    </div>
    <div class="div-link-preview-col div-link-preview-col-r">
        <div style="display: block; height: 100%; padding-left: 10px;">
            <div class="div-link-preview-title"><a href="{page_link:}">{page_title:}</a></div>
            <div class="div-link-preview-content">{page_description:}</div>
            <div class="div-link-preview-domain">
            <span style="font-size: 100%; margin-left: 20px;">&#x1F517;</span>&nbsp;{page_domain:}</div>
        </div>
    </div>
</div>
'''

# CSS style sheet for the HTML code in linkPreviewTemplate.
css = """
.div-link-preview {
    margin-left: auto;
    margin-right: auto;
    overflow: hidden;
    width: 50%;
    margin-bottom: 10px;
    background-color: white;
}

.div-link-preview:after {
    content: "";
  display: table;
  clear: both;
}

.div-link-preview-col {
    float: left;
}

.div-link-preview-col-l {
    width: 18%
}

.div-link-preview-col-r {
    width: 60%;
    padding-top: 5px;
}


.div-link-preview-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}


.div-link-preview-content::-webkit-scrollbar {
    width: 0px;
    background: yellow; /* Chrome/Safari/Webkit */
}

.div-link-preview-title {
    display: block;
    margin-right: auto;
    width: 98%;
    font-weight: bold;
    font-size: x-large;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #101010;
    line-height: 150%;
}

.div-link-preview-title a{
    color: #101010;
}

.div-link-preview-content {
    display: block;
    font-size: large;
    height: 58%;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #606060;
}

.div-link-preview-domain {
    padding-right: 2%;
    display: block;
    font-weight: bold;
    color: #808080;
    text-align: right;
    font-size: 100%;
    font-family: Helvetica, sans-serif;
}
"""

# JavaScript used to adjust the aspect ratio of the preview. Meant to be appended to the end of the HTML code.
aspectRatioScript = """
<script>
        function adjustLinkPreviewHeight(){
          console.log("running!");
          var cats = document.querySelectorAll('.div-link-preview');
          //console.log(cats.length);
          for (var i = 0; i < cats.length; i++) {
            var left = cats[i].querySelector('.div-link-preview-col-l');
            var right = cats[i].querySelector('.div-link-preview-col-r');
            var width = left.clientWidth;
            cats[i].style.height = width + "px";
            left.style.height = width + "px";
            right.style.height = width + "px";
          }
        }

        adjustLinkPreviewHeight();
</script>
"""

# Extra html used to adjust the font of the title and body for the preview. Kept separate so .format() works with linkPreviewTemplate.
fontAdjust = """
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
    body {
        font-family: 'Inter', sans-serif;
        color: #111111;
    }
</style>
</head>
<body>
"""

# Returns HTML code to create an image preview for the link provided.
# If the argument given is not a valid url, returns an image preview for 
# a Google search of the argument.
# @param url A string containing the url to make the preview for.
# @return The HTML code containing the completed image preview.
def preview(url):
    if not validators.url(url):
        googleUrl = "https://www.google.com/search?q={}".format(url)
        link = linkPreview(googleUrl)
        return fontAdjust + linkPreviewTemplate.format(img_link="https://www.google.com/images/branding/googleg/1x/googleg_standard_color_128dp.png", 
                                                       page_title=link.title, 
                                                       page_link=googleUrl, 
                                                       page_description='Search for "{}" on Google'.format(url), 
                                                       page_domain=urlparse(googleUrl).netloc) + "\n</body>\n</html>\n"
    link = linkPreview(url)
    return fontAdjust + linkPreviewTemplate.format(img_link=link.image, 
                                      page_title=link.title, 
                                      page_link=url, 
                                      page_description=link.description, 
                                      page_domain=urlparse(url).netloc) + "\n</body>\n</html>\n"

# Saves a .png screenshot of the generated image preview to the designated path.
# @param url A string containing the url to make the preview for.
# @param path A string containing the desired filename for the image (Will be saved in the 'images' folder).
def generateLinkPreview(url, path):
    # Generating the HTML code and appending the JavaScript at the end.
    html = preview(url) + aspectRatioScript
    hti.screenshot(html_str=html, css_str=css, save_as=path)
    # Cropping the screenshot to remove any whitespace.
    im = Image.open('images/' + path)
    im.crop((484, 8, 1248, 179)).save('images/' + path, quality=95)