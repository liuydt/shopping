import re

class UnitPrice:

    def parse_unit_price(self, price:str) -> str:
        """parse unit price to standard unit price across all merchants.

        Args:
            price (str): price of the items with both price and unit.

        Returns:
            str: string representation of standard unit price across all merchants
        """
        price = re.sub('[(|)]','',price)
        if '/' in price:
            price_list = price.split('/')
        elif 'per' in price:
            price_list = price.split('per')
        else:
            price_list = price.split(' ')

        self._parse_price(price_list[0].strip())
        
        if len(price_list) > 1:
            self._parse_unit(price_list[1].strip())
        else:
            self.unit = 'unknown_unit'
        
        return '£' + str(self.price) + '/' + self.unit

    def _parse_price(self, price:str) -> None:
        """parse pence price to £ price

        Args:
            price (str): price of the item that can be pound amount or pence amount
        """

        numbers = re.findall(r"\d+\.?\d*", price)

        if 'p' in price:            
            self.price = round(float(''.join(numbers))/100, 2)
        else:
            self.price = round(float(''.join(numbers)), 2)
    
    def _parse_unit(self, unit:str) -> None:
        """parse unit to standard unit

        Args:
            unit (str): unit of the items. 
        """
        if re.match('mr|mtr|metre', unit):
            self.unit = 'metre'
        elif re.match('(\\d+)g', unit):
            self.unit = 'kg'
            self.price = self.price * 1000 / float(re.search('(\\d+)g', unit)[1])
        elif re.match('kg', unit):
            self.unit = 'kg'
        elif re.match('75cl', unit):
            self.unit = '75cl'
        elif re.match('100sht', unit):
            self.unit = '100sht'
        elif re.match('lt|ltr|litre', unit):
            self.unit = 'litre'
        elif re.match('(\\d+)ml', unit):
            self.unit = 'litre'
            self.price = self.price * 1000 / float(re.search('(\\d+)ml', unit)[1])
        elif re.match('each|ea', unit):
            self.unit = 'each'
        else:
            self.unit = 'unknown_unit'

    def __str__(self) -> str:
        """get string presentation of price per unit

        Returns:
            str: string presentation of price per unit.
        """
        return f"price={self.price}, unit={self.unit}"