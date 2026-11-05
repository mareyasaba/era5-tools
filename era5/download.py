"""Downloads ERA5 monthly-mean data for GRTCODE from the (new, 2024+) Copernicus Data Store."""
from collections import namedtuple

from cdsapi import Client

from .commands import Command


class Download(Command):
    @staticmethod
    def arguments(subparsers):
        """Adds command specific command-line arguments.

        Args:
            subparsers: Special action object returned by ArgumentParser().add_subparsers().
        """
        command = "download"
        parser = subparsers.add_parser(command, help="{} help.".format(command))
        parser.add_argument("level_file", help="output file path for pressure level data.")
        parser.add_argument("single_file", help="output file path for single level data.")
        parser.add_argument("-y", help="Starting year.", type=int, required=True)
        parser.add_argument("-Y", help="Ending year.", type=int, required=True)
        parser.add_argument("-m", help="Starting month.", type=int, default=1)
        parser.add_argument("-M", help="Ending month.", type=int, default=12)
        parser.set_defaults(func=download_)


def download_(args):
    """Command-line wrapper around download()."""
    download(args.level_file, args.single_file, args.y, args.Y, args.m, args.M)


def download(level_output, single_output, start_year, end_year, start_month, end_month):
    """Download ERA5 monthly averaged data from the Copernicus Data Store (CDS).

    Requires a CDS account and credentials in $HOME/.cdsapirc.

    Args:
        level_output: Output file path for pressure level data.
        single_output: Output file path for single level data.
        start_year: Starting year (inclusive).
        end_year: Ending year (inclusive).
        start_month: Starting month (inclusive).
        end_month: Ending month (inclusive).
    """
    client = Client()

    Product = namedtuple("Product", ("type", "level_name", "single_name"))
    monthly = Product(
        type="monthly_averaged_reanalysis",
        level_name="reanalysis-era5-pressure-levels-monthly-means",
        single_name="reanalysis-era5-single-levels-monthly-means"
    )

    years = [str(x) for x in range(start_year, end_year + 1)]
    months = ["{:02}".format(x) for x in range(start_month, end_month + 1)]

    # Pressure level variables read by GRTCODE (era5/src/era5.c).
    level_variables = [
        "ozone_mass_mixing_ratio", "specific_humidity", "temperature",
        "fraction_of_cloud_cover", "specific_cloud_ice_water_content",
        "specific_cloud_liquid_water_content"
    ]
    # Note: the new CDS returns these in descending order (1000 -> 1 hPa);
    # vertical_remap.py sorts them, so the order here does not matter.
    pressure_levels = [
        1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 125, 150, 175, 200,
        225, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750,
        775, 800, 825, 850, 875, 900, 925, 950, 975, 1000
    ]
    retrieve(client, monthly.level_name, monthly.type, level_output,
             level_variables, years, months, pressure_levels=pressure_levels)

    # Surface and TOA variables read by GRTCODE (era5/src/era5.c): sp, skt, t2m, fal, tisr.
    # Raymond's original also fetched ERA5's own radiative fluxes and UV/NIR albedos for
    # validation; GRTCODE does not read them, so they are not downloaded here.
    single_variables = [
        "skin_temperature",
        "surface_pressure",
        "2m_temperature",
        "forecast_albedo",
        "toa_incident_solar_radiation"
    ]
    retrieve(client, monthly.single_name, monthly.type, single_output,
             single_variables, years, months)


def retrieve(client, dataset_name, product_type, target_file, variables, years, months,
             pressure_levels=None):
    """Helper function to perform a CDS retrieval."""
    request = {
        "product_type": product_type,
        "variable": variables,
        "year": years,
        "month": months,
        "time": "00:00",
        "data_format": "netcdf",
        "download_format": "unarchived"
    }
    if pressure_levels:
        request["pressure_level"] = [str(p) for p in pressure_levels]
    client.retrieve(dataset_name, request, target_file)
