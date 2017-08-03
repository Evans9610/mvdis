# Query car efficacy by seq

import concurrent.futures
import json
import requests
from collections import namedtuple
from lxml import etree


class CarEfficacy(object):
    INDEX_URL = 'https://www.mvdis.gov.tw/m3-emv-mk3/tourBus/'
    COUNTING_URL = '%squery' % INDEX_URL
    QUERY_URL = '%squery?method=carEfficacy&seq={seq}&num={num}' % INDEX_URL
    CarEfficacyDetail = namedtuple('CarEfficacyDetail', 'seq num bodyNo manufacturers date isOverdue violations insurance horsepower torque length width weight displacement abs auxiliaryBrakes gps ')

    def __init__(self):
        self.session = requests.Session()
        self.data = []
        self.seq = 0

    def _get_car_amount(self):
        # Get the company's amount of cars
        resp = self.session.post(self.COUNTING_URL,
                                 data={"method": "queryCarDetail",
                                       "seq": self.seq})
        root = etree.HTML(resp.text)
        data = root.xpath('//input[@name="txtPage"]')   # paging label

        data = data[0].tail.split(' ')
        num = data[data.index("筆資料")-1]

        if not num.isdigit():
            return 0

        return int(num)

    def _get_car_page(self, num):
        # Get CarEfficacy page data
        resp = self.session.get(self.QUERY_URL.format(seq=self.seq, num=num))
        root = etree.HTML(resp.text)
        data = root.xpath('//table[@class="tb_list_std gap_b2 gap_t"]//td')

        if not data:
            raise ValueError

        def _make_data(d):
            return [str(self.seq), str(num)] + [x.text.strip() for x in d]

        self.data.append(self.CarEfficacyDetail(*_make_data(data)))

    def getCars(self, seq):
        self.seq = seq
        car_amount = self._get_car_amount()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for num in range(1, car_amount+1):
                executor.submit(self._get_car_page, num)

        return self.data


if __name__ == '__main__':
    t = CarEfficacy()
    print(t.getCars(206))
    print(t.getCars(230))
