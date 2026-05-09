# Open Source Guide

## Purpose

`exif-mcp-server` is a practical, production-leaning sample MCP server for EXIF
inspection and cleanup.

It is intended to be useful in two ways:

- as a real local EXIF utility for MCP clients
- as a reference implementation for people learning how to build MCP servers

## Scope

This project focuses on:

- EXIF metadata only
- stable tool contracts
- safe local file handling
- clear examples for MCP clients

## Non-Goals

This project does not currently target:

- cloud uploads
- user accounts
- databases
- IPTC editing
- XMP editing
- unrelated image processing

## Safety Defaults

- read-only tools never modify files
- cleaned outputs are written to sibling files by default
- existing files are not overwritten unless `overwrite=true`
- batch operations continue on per-file failures

## Teaching Value

This repo is structured to make the main MCP patterns easy to study:

- shared core logic
- thin MCP adapter
- explicit tool contracts
- stable JSON outputs
- tests and CI
