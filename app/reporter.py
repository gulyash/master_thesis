import datetime

from fpdf import FPDF


class ReportTemplate(FPDF):

    def __init__(self, test_info, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        date = datetime.datetime.today()
        self.header_data = {
            'mold_type': test_info.mold_type,
            'tester_name': test_info.tester_name,
            'date': date.strftime('%Y.%m.%d %H:%M'),
            'mold_no': test_info.mold_no,
            'report_status_image': test_info.report_status_image,
        }
        self.signature_data = {
            'tester_name': test_info.tester_name,
            'signature_date': date.strftime('%Y.%m.%d')
        }
        self.test_data = test_info.data

    def place_vertical_text(self, text, x, y, cell_width, cell_height=0, align='C'):
        self.set_xy(x, y)
        self.rotate(90)
        self.cell(cell_width, cell_height, text, align=align)
        self.set_xy(0, 0)
        self.rotate(0)

    def load_custom_fonts(self, fonts):
        for font_name, font_path in fonts.items():
            self.add_font(font_name, '', font_path, uni=True)

    def place_header_field(self, field_name, field_value, name_width, value_width, header_row_height, text_size=10):
        self.set_font('OpenSans-Regular', size=text_size)
        self.cell(name_width, header_row_height, field_name)
        self.set_font('OpenSans-Bold', size=text_size)
        self.cell(value_width, header_row_height, field_value, 0, 0, 'R')

    def draw_title(self,
                   title_text,
                   title_font='RobotoCondensed-Bold',
                   title_font_size=18,
                   title_cell_height=15):
        self.set_font(title_font, size=title_font_size)
        self.cell(0, title_cell_height, txt=title_text, ln=1, align="C")

    def draw_header(self,
                    data,
                    x_start=15,
                    x_end=195,
                    logo_width=40,
                    logo_offset=4,
                    first_line_y_offset=25,
                    header_row_height=10,
                    spacer_width=5,
                    line_rgb=(112, 112, 112,),
                    status_image_width=5,
                    date_width=15,
                    date_value_width=40,
                    status_width=15,
                    status_value_width=10,
                    mold_type_width=25,
                    mold_type_value_width=60,
                    tester_width=15,
                    tester_value_width=25):
        second_line_x_end = x_end - logo_width - logo_offset * 2
        second_line_y_offset = first_line_y_offset + header_row_height
        third_line_y_offset = first_line_y_offset + header_row_height * 2

        # draw lines
        self.set_draw_color(*line_rgb)
        self.line(x_start, first_line_y_offset, x_end, first_line_y_offset)
        self.line(x_start, second_line_y_offset, second_line_x_end, second_line_y_offset)
        self.line(x_start, third_line_y_offset, x_end, third_line_y_offset)
        self.set_draw_color(0, 0, 0)

        # draw logo
        logo_x = second_line_x_end + logo_offset
        logo_y = first_line_y_offset + header_row_height * 2 / 3
        self.image('static/images/SMSGroup.png', logo_x, logo_y, w=logo_width)

        # first line: mold type and tester
        self.set_xy(x_start, first_line_y_offset)
        self.place_header_field('Mold type', data['mold_type'], mold_type_width, mold_type_value_width,
                                header_row_height)
        self.cell(spacer_width, header_row_height)
        self.place_header_field('Tester', data['tester_name'], tester_width, tester_value_width, header_row_height)

        # second line
        self.set_xy(x_start, second_line_y_offset)
        # draw date
        self.place_header_field('Date', data['date'], date_width, date_value_width, header_row_height)
        self.cell(spacer_width, header_row_height)
        # draw status
        status_offset = x_start + date_width + date_value_width + spacer_width
        status_image_x_offset = status_offset + status_width + status_value_width - status_image_width
        status_image_y_offset = second_line_y_offset + header_row_height / 2 - status_image_width / 2
        self.place_header_field('Status', '', status_width, status_value_width, header_row_height)
        self.image(data['report_status_image'], status_image_x_offset, status_image_y_offset,
                   w=status_image_width)
        self.cell(spacer_width, header_row_height)
        # draw mold_no
        self.place_header_field('Mold No.', data['mold_no'], 20, 20, header_row_height)

    def header(self):

        self.load_custom_fonts({
            'RobotoCondensed-Bold': 'static/fonts/RobotoCondensed-Bold.ttf',
            'OpenSans-Regular': 'static/fonts/OpenSans-Regular.ttf',
            'OpenSans-Bold': 'static/fonts/OpenSans-Bold.ttf'
        })
        # draw title
        self.draw_title("MOLD SENSOR DIAGNOSTICS - TEST REPORT")
        # draw header
        self.draw_header(self.header_data)

    def footer(self):
        self.set_y(-25)
        text_size = 8
        self.set_font('OpenSans-Regular', size=text_size)
        self.cell(170, 0, 'Page ', 0, 0, 'R')
        self.set_font('OpenSans-Bold', size=text_size)
        # Add a page number
        page = str(self.page_no()) + ' of {nb}'
        self.cell(10, 0, page, 0, 0)

    def draw_result_containers(self, rp):
        # right
        self.rect(rp.first_x_offset, rp.upper_y_offset, rp.rectangle_width, rp.narrow_rectangle_height)
        # fixed
        self.rect(rp.first_x_offset, rp.fixed_y_offset, rp.rectangle_width, rp.wide_rectangle_height)
        # loose
        self.rect(rp.second_x_offset, rp.upper_y_offset, rp.rectangle_width, rp.wide_rectangle_height)
        # left
        self.rect(rp.second_x_offset, rp.left_y_offset, rp.rectangle_width, rp.narrow_rectangle_height)

        self.set_font('RobotoCondensed-Bold', size=14)
        for text, text_x_offset, text_y_offset, cell_width in [
            ("FIXED", rp.first_text_x_offset, rp.lower_y_offset, rp.wide_rectangle_height),
            ("RIGHT", rp.first_text_x_offset, rp.right_text_y_offset, rp.narrow_rectangle_height),
            ("LOOSE", rp.second_text_x_offset, rp.loose_text_y_offset, rp.wide_rectangle_height),
            ("LEFT", rp.second_text_x_offset, rp.lower_y_offset, rp.narrow_rectangle_height)
        ]:
            self.place_vertical_text(text, text_x_offset, text_y_offset, cell_width)

    def draw_place_for_signature(self,
                                 line_x_offset=185,
                                 line_y_upper=57,
                                 line_y_lower=95,
                                 date_cell_width=35,
                                 ):
        date_cell_y_offset = line_y_lower + date_cell_width
        tester_name_x_offset = line_x_offset + 3
        line_length = line_y_lower - line_y_upper
        self.line(line_x_offset, line_y_upper, line_x_offset, line_y_lower)
        self.set_font('OpenSans-Regular', size=10)
        self.place_vertical_text(self.signature_data['signature_date'], line_x_offset - 1, date_cell_y_offset,
                                 date_cell_width, align='R')
        self.place_vertical_text(self.signature_data['tester_name'], tester_name_x_offset, line_y_lower,
                                 line_length)

    def draw_side_results(self, mold_side, image_horizontal_offset, image_vertical_offset):
        column_width = 12
        row_height = 15
        image_width = 5
        text_horizontal_offset = image_horizontal_offset + 8

        self.set_xy(0, 0)
        self.rotate(90, 0, 0)
        for tc_info in self.test_data[mold_side]:
            vertical_offset = image_vertical_offset - tc_info['column'] * column_width
            horizontal_offset = image_horizontal_offset + tc_info['row'] * row_height
            self.image(tc_info['image'], -vertical_offset, horizontal_offset, w=image_width)
        self.set_xy(0, 0)
        self.rotate(0)

        self.set_font('RobotoCondensed-Bold', size=11)
        for tc_info in self.test_data[mold_side]:
            vertical_offset = image_vertical_offset - tc_info['column'] * column_width
            horizontal_offset = text_horizontal_offset + tc_info['row'] * row_height
            self.place_vertical_text(str(tc_info['label']), horizontal_offset, vertical_offset, image_width)

    def draw_test_results(self, rp):
        # paddings between rectangle and left lower image
        horizontal_padding = 10
        vertical_padding = 26
        for mold_side, first_image_horizontal_offset, first_image_vertical_offset in [
            ("Fixed", rp.first_x_offset + horizontal_padding, rp.lower_y_offset - vertical_padding),
            ("Loose", rp.second_x_offset + horizontal_padding, rp.loose_text_y_offset - vertical_padding),
            ("Right", rp.first_x_offset + horizontal_padding, rp.right_text_y_offset - vertical_padding / 4),
            ("Left", rp.second_x_offset + horizontal_padding, rp.lower_y_offset - vertical_padding / 4)
        ]:
            self.draw_side_results(mold_side, first_image_horizontal_offset, first_image_vertical_offset)

    def generate_report(self):
        class ReportProps:
            def __init__(self,
                         first_x_offset=27,
                         second_x_offset=105,
                         rectangle_width=63,
                         narrow_rectangle_height=30,
                         wide_rectangle_height=155,
                         upper_y_offset=55,
                         vertical_spacing=10,
                         text_above_box=5
                         ) -> None:
                super().__init__()
                self.first_x_offset = first_x_offset
                self.second_x_offset = second_x_offset
                self.rectangle_width = rectangle_width
                self.narrow_rectangle_height = narrow_rectangle_height
                self.wide_rectangle_height = wide_rectangle_height
                self.upper_y_offset = upper_y_offset
                self.lower_y_offset = upper_y_offset + narrow_rectangle_height + vertical_spacing + wide_rectangle_height
                self.vertical_spacing = vertical_spacing
                self.fixed_y_offset = upper_y_offset + narrow_rectangle_height + vertical_spacing
                self.left_y_offset = upper_y_offset + wide_rectangle_height + vertical_spacing
                self.text_above_box = text_above_box
                self.first_text_x_offset = first_x_offset - text_above_box
                self.second_text_x_offset = second_x_offset - text_above_box
                self.right_text_y_offset = upper_y_offset + narrow_rectangle_height
                self.loose_text_y_offset = upper_y_offset + wide_rectangle_height

        # create alias for page numeration
        self.alias_nb_pages()
        # add first page with auto-created header and footer
        self.add_page()
        self.draw_place_for_signature()
        rp = ReportProps()
        self.draw_result_containers(rp)
        self.draw_test_results(rp)


class TestInfo:
    def __init__(self, tester_name, mold_type, mold_no, data, report_status_image) -> None:
        super().__init__()
        self.tester_name = tester_name
        self.mold_type = mold_type
        self.mold_no = mold_no
        self.data = data
        self.report_status_image = report_status_image


def generate_report(filename, test_data, mold_no, mold_type, tester_name):
    def get_side_info(x_list, y_list, label_list, status_list):
        y_map = {
            y: row for row, y in enumerate(sorted(set(y_list), reverse=True))
        }
        x_map = {
            x: column for column, x in enumerate(sorted(set(x_list)))
        }
        data = [{
            'column': x_map[x],
            'row': y_map[y],
            'label': label,
            'image': image_map[status],
        } for x, y, label, status in zip(x_list, y_list, label_list, status_list)]
        return data

    image_map = {
        "success": "static/images/Success.png",
        "fail": "static/images/Failed.png",
        "OK": "static/images/NotTested.png",
        "Disconnected": "static/images/Failed.png"
    }

    if all(status == "success" for mold_side in test_data.keys() for status in test_data[mold_side]['status']):
        report_status = "success"
    else:
        report_status = "fail"
    report_status_image = image_map[report_status]
    layout = {
        mold_side: get_side_info(test_data[mold_side]['x'], test_data[mold_side]['y'], test_data[mold_side]['label'],
                                 test_data[mold_side]['status']) for mold_side in test_data.keys()
    }
    test_info = TestInfo(tester_name, mold_type, mold_no, layout, report_status_image)
    pdf = ReportTemplate(test_info, format='A4')
    pdf.generate_report()
    pdf.output(f"static/reports/{filename}.pdf")
