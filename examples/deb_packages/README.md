# Overview

This folder contains examples on how to use `deb_packages` rules in practice.

## `deb_packages_base`

Two docker images (`base`/`debug`) that contain the same packages as the distroless base image from https://github.com/GoogleCloudPlatform/distroless using the `deb_packages` rules.

It creates Jessie and Stretch versions of these containers.
