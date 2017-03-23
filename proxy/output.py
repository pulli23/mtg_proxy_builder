import math as m
import os
from typing import Dict, Union, Tuple
import typing

import jinja2

from proxy import paper
import mylogger
logger = mylogger.MAINLOGGER


class OutputLatex:
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

    def __init__(self, image_directory: str = "", mypaper: Union[str, paper.Paper] = "a4paper",
                 card_dimensions: Tuple[float, float] = None, cut_thickness: float = 0,
                 cut_color: str="black", background_color: str="black", **kwargs):
        self.cut_color = cut_color
        self.cut_thickness = cut_thickness
        self.background_color = background_color
        self.image_directory = image_directory
        if card_dimensions is None:
            card_dimensions = (63 - 2, 88 - 2)
        self.card_dimensions = card_dimensions
        self.latexstr = None
        self.mypaper = None
        self.cardlayout = None
        self.paper_orientation = type(self).PORTRAIT
        self.images = None
        self.load_image_list({})
        self.load_paper_settings(mypaper)
        self.extra_settings = kwargs

    def load_paper_settings(self, mypaper):
        if isinstance(mypaper, str):
            mypaper = paper.Paper(name=mypaper)
        self.mypaper = mypaper
        x = mypaper.width - mypaper.margins[0] * 2
        y = mypaper.height - mypaper.margins[1] * 2
        cut_thickness = self.cut_thickness
        card_dimensions = self.card_dimensions
        if m.floor((x + cut_thickness) / (card_dimensions[0] + cut_thickness)) * \
                m.floor((y + cut_thickness) / (card_dimensions[1] + cut_thickness)) >= \
                        m.floor((x + cut_thickness) / (card_dimensions[1] + cut_thickness)) * \
                        m.floor((y + cut_thickness) / (card_dimensions[0] + cut_thickness)):
            self.paper_orientation = type(self).PORTRAIT
            self.cardlayout = (m.floor((x + cut_thickness) / (card_dimensions[0] + cut_thickness)),
                               m.floor((y + cut_thickness) / (card_dimensions[1] + cut_thickness)))
        else:
            self.paper_orientation = type(self).LANDSCAPE
            self.cardlayout = (m.floor((y + cut_thickness) / (card_dimensions[0] + cut_thickness)),
                               m.floor((x + cut_thickness) / (card_dimensions[1] + cut_thickness)))

    def save(self, target: typing.io.TextIO, latexstr: str = None):
        logger.info("Saving latex ({0})...".format(target))
        if latexstr is None:
            if self.latexstr is None:
                raise ValueError("Latex not generated")
            latexstr = self.latexstr
        target.write(latexstr)
        logger.info("Saving latex, done!")

    def load_image_list(self, images: Dict[str, int]):
        image_list = []
        for img, num in images.items():
            image_list.extend([os.path.join(self.image_directory, img)] * num)
        self.images = image_list

    def create_latex(self, template_name):
        self.latexstr = self._create_latex(template_name)

    def _create_latex(self, template_name: str, **kwargs) -> str:
        print("Creating latex ({0})...".format(template_name))
        latex_jinja_env = jinja2.Environment(
            block_start_string='\BLOCK{',
            block_end_string='}',
            variable_start_string='\VAR{',
            variable_end_string='}',
            comment_start_string='\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(os.path.abspath('.'))
        )
        mypaper = self.mypaper
        cardlayout = self.cardlayout
        card_dimensions = self.card_dimensions
        image_list = self.images
        template = latex_jinja_env.get_template(template_name)
        namestr = mypaper.name
        if namestr is None:
            namestr = "paperwidth={0}mm,paperheight={1}mm".format(mypaper.width, mypaper.height)

        lastr = template.render(paper=namestr,
                                orientation=self.paper_orientation,
                                hmargin=mypaper.margins[0],
                                vmargin=mypaper.margins[1],
                                num_img_hor=cardlayout[0],
                                num_img_ver=cardlayout[1],
                                images=[os.path.splitext(img)[0].replace('\\', '/') for img in image_list],
                                img_width=card_dimensions[0],
                                img_height=card_dimensions[1],
                                cut_thickness=self.cut_thickness,
                                cut_color=self.cut_color,
                                background_color=self.background_color,
                                **{**self.extra_settings, **kwargs})
        logger.info("Writing latex: done!")
        return lastr

    def __call__(self, fileobj: typing.io.TextIO, template_name: str, *args, **kwargs):
        latexstr = self._create_latex(template_name)
        self.save(fileobj, latexstr)

