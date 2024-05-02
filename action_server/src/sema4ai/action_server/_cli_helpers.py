def add_data_args(parser, defaults):
    parser.add_argument(
        "-d",
        "--datadir",
        metavar="PATH",
        default="",
        help=(
            "Directory to store the data for operating the actions server "
            "(by default a datadir will be generated based on the current directory)."
        ),
    )
    parser.add_argument(
        "--db-file",
        help=(
            "The name of the database file, relative to the datadir "
            "(default: %(default)s)"
        ),
        default=defaults["db_file"],
    )


def add_verbose_args(parser, defaults):
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Be more talkative (default: %(default)s)",
    )


def add_login_args(parser):
    parser.add_argument(
        "-a",
        "--access-credentials",
        type=str,
        help="Control Room access credentials",
        required=False,
    )
    parser.add_argument(
        "--hostname", type=str, help="Hostname for the Control Room URL", required=False
    )


def add_organization_args(parser):
    parser.add_argument(
        "-o",
        "--organization-id",
        type=str,
        help="Control Room organization ID",
        required=True,
    )


def add_push_package_args(parser):
    parser.add_argument(
        "-p",
        "--package-path",
        type=str,
        help="Path to the uploaded package",
        required=True,
    )


def add_package_args(parser):
    parser.add_argument(
        "-i",
        "--package-id",
        type=str,
        help="Control Room action package ID",
        required=True,
    )


def add_publish_args(parser):
    parser.add_argument(
        "-c",
        "--change-log",
        type=str,
        help="Changelog string for published package",
        required=True,
    )


def add_json_output_args(parser):
    parser.add_argument(
        "--json",
        help="Write output to stdout in json format",
        action="store_true",
    )
