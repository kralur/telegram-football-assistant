def paginate(items: list[dict], page: int, page_size: int):
    if not items:
        return [], 0, 1

    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    end = start + page_size
    return items[start:end], page, total_pages
