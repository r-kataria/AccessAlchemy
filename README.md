# AccessAlchemy

AccessAlchemy is a project I put together to explore how obtaining additional visas and travel documents can significantly boost the strength of a passport. By analyzing visa requirements and access levels, the project demonstrates how strategic acquisitions of visas can expand global mobility for travelers.

## Purpose

The main idea is to see how different visas, residence permits, and passports interact to provide varying levels of access to countries worldwide. Using data from [Wikipedia's Visa Requirements for Indian Citizens](https://en.wikipedia.org/wiki/Visa_requirements_for_Indian_citizens), I wanted to visualize and analyze the impact of adding certain documents to an Indian passport.

## Technical Overview

At its core, AccessAlchemy is a computer science project that heavily relies on graph theory. I used Python along with the NetworkX library to model the relationships between documents and countries. In this graph:

- **Nodes** represent either travel documents (like passports, visas, or residence permits) or countries.
- **Edges** represent the access type that a document grants to a country (such as visa-free entry, eVisa eligibility, etc.).

By constructing and analyzing this graph, I could perform various computations, like finding the best single visa to visit a specific country or determining the minimal set of visas required to maximize global access. The project includes functions to summarize accessible countries, suggest the next best documents to obtain, and rank documents based on their benefits.

## Examples

Some of the things you can do with AccessAlchemy include:

- **Find accessible countries**: Given a set of documents, see which countries you can access without needing a visa.
- **Best visa for a country**: Discover the best visa to get if you want to visit a particular country and see what other benefits it provides.
- **Minimum visas for maximum access**: Calculate the minimal set of visas that covers the most countries.
- **Suggest next documents**: Get suggestions on which documents to obtain next to enhance your passport strength.

## TODO

I know the code needs better organization, so I'm planning to refactor it to make it cleaner and more modular. I'm also thinking about creating a GUI to make it easier to interact with and visualize the results, making the exploration of visa options more accessible. Additionally, I need to extend the data to include access requirements for other passports, such as the Chinese passport.

## Data Source

All the visa requirement data comes from [Wikipedia's Visa Requirements for Indian Citizens](https://en.wikipedia.org/wiki/Visa_requirements_for_Indian_citizens). It provides up-to-date information on visa policies affecting Indian passport holders.

## Find This Interesting?

If you find AccessAlchemy useful, please give it a star on GitHub! 🌟

Feel free to submit a pull request or open an issue to share your ideas and improvements.