from m3u_parser import M3uParser


def main() -> None:
    url = "./ru.m3u"
    useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

    parser = M3uParser(timeout=20, useragent=useragent)

    parser.parse_m3u(url)
    parser.filter_by('status', 'GOOD')

    print(len(parser.get_list()))

    parser.to_file('streams.m3u')


if __name__ == '__main__':
    main()
