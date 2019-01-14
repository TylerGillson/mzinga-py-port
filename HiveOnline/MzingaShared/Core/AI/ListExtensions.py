class ListExtensions:
    @staticmethod
    def get_enumerable_by_order_type(items, order_type):
        length = items.count
        i = 1 if order_type == "SkipOffset" and length > 1 else 0

        count = 0
        out = []
        while i < length:
            out.append(items[i])

            count += 1
            i += 1 if order_type == "Default" else 2

            if count < length <= i:
                i = 0 if order_type == "SkipOffset" else 1
        return out
