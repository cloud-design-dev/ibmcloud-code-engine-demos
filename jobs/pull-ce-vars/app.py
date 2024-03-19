#!/usr/bin/env python3

import os
import json
from datetime import datetime
import click
import base64

@click.group()
def cli():
    """Group to hold our commands"""
    pass


@cli.command()
def pull_bound_services():
    """Pulls all CE_SERVICES variable keys"""
    ce_services_json = os.environ.get('CE_SERVICES')
    if ce_services_json:
        ce_services_dict = json.loads(ce_services_json)
        ce_keys = ce_services_dict.keys()
        for key in ce_keys:
            print(key)
    else:
        click.echo("CE_SERVICES is not set or is empty")
        return None


@cli.command()
def pull_bound_services_and_keys():
    """Pulls all CE_SERVICES variables and their values"""
    ce_services_json = os.environ.get('CE_SERVICES')
    if ce_services_json:
        ce_services_dict = json.loads(ce_services_json)
        return ce_services_dict.items()
    else:
        click.echo("CE_SERVICES is not set or is empty")
        return None

@cli.command()
def pull_all_env_vars():
    """Pulls all environment variables"""
    for name, value in os.environ.items():
        click.echo(f"{name}: {value}\n")

if __name__ == '__main__':
    cli()
