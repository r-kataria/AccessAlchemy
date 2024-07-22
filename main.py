import json
import networkx as nx
from itertools import combinations
from collections import defaultdict
from rich import print
from rich.table import Table
from rich.console import Console

# Initialize Rich console
console = Console()

visa_data = json.load(open('data.json'))

# Initialize the graph
G = nx.DiGraph()

# Add nodes and edges with categories
for country, docs in visa_data.items():
    for doc, access_type in docs.items():
        # Determine the category of the document
        if "Passport" in doc:
            category = "passport"
        elif "Green Card" in doc:
            category = "residence_permit"
        elif "Visa" in doc:
            category = "visa"
        else:
            category = "visa"  # Default to visa if unsure
        
        G.add_node(doc, type='document', category=category)
        G.add_node(country, type='country')
        G.add_edge(doc, country, access_type=access_type)

# Define access hierarchy
access_hierarchy = {
    "freedom_of_movement": 4,
    "visa_free": 3,
    "evisa": 2,
    "visa_required": 1
}

def get_accessible_countries(visa_set):
    """
    Given a set of visas, return a dictionary of accessible countries with the highest access tier,
    excluding 'visa_required' access types.
    """
    accessible = defaultdict(dict)
    for visa in visa_set:
        if visa not in G:
            continue
        for neighbor in G.successors(visa):
            edge_data = G.get_edge_data(visa, neighbor)
            access_type = edge_data.get('access_type', 'visa_required')
            if access_type == 'visa_required':
                continue  # Skip visa_required access
            current_access = accessible[neighbor].get('access_type', 'none')
            # Update if the new access type is higher in hierarchy
            if access_hierarchy.get(access_type, 0) > access_hierarchy.get(current_access, 0):
                accessible[neighbor]['access_type'] = access_type
    return accessible

def summarize_access(visa_set):
    """
    Summarize the number of countries under each accessible tier, excluding 'visa_required'.
    """
    accessible = get_accessible_countries(visa_set)
    summary = defaultdict(int)
    for country, data in accessible.items():
        summary[data['access_type']] += 1
    return summary

def list_accessible_countries(visa_set):
    """
    List all accessible countries with their access types, excluding 'visa_required'.
    """
    accessible = get_accessible_countries(visa_set)
    return accessible

def find_best_visa_for_country(target_country):
    """
    Find the best single visa to visit the target country.
    The best visa is defined as the one that provides the highest access level
    to the target country and also grants access to the most other countries.
    """
    best_visas = []
    best_access_level = 0
    for doc, access_type in visa_data.get(target_country, {}).items():
        level = access_hierarchy.get(access_type, 0)
        if level > best_access_level:
            best_access_level = level
            best_visas = [doc]
        elif level == best_access_level:
            best_visas.append(doc)
    
    # If multiple visas have the same access level, choose the one with the most overall coverage
    if len(best_visas) > 1:
        visa_coverage = {}
        for visa in best_visas:
            # Count only accessible countries (excluding visa_required)
            coverage = len([n for n in G.successors(visa) if G[visa][n]['access_type'] != 'visa_required'])
            visa_coverage[visa] = coverage
        # Sort visas by coverage descending
        sorted_visas = sorted(visa_coverage.items(), key=lambda x: x[1], reverse=True)
        best_visa = sorted_visas[0][0]
    else:
        best_visa = best_visas[0] if best_visas else None
    
    # Gather additional benefits
    additional_countries = [n for n in G.successors(best_visa) if G[best_visa][n]['access_type'] != 'visa_required']
    total_additional = len(additional_countries)
    
    return best_visa, [k for k, v in access_hierarchy.items() if v == best_access_level][0] if best_visas else (None, None), additional_countries

def find_min_visas_to_cover_all():
    """
    Find the minimum set of visas required to cover all countries with at least 'freedom_of_movement',
    'visa_free', or 'evisa_on_arrival' access.
    Uses a greedy approach.
    """
    all_countries = set(visa_data.keys())
    # Exclude passports from being selected as visas
    visas = [doc for doc in G.nodes if G.nodes[doc]['type'] == 'document' and G.nodes[doc]['category'] == 'visa']
    # Include residence permits as they are similar to visas in access
    residence_permits = [doc for doc in G.nodes if G.nodes[doc]['type'] == 'document' and G.nodes[doc]['category'] == 'residence_permit']
    visas.extend(residence_permits)
    
    uncovered = set(all_countries)
    selected_visas = set()

    while uncovered:
        best_visa = None
        covered = set()
        for visa in visas:
            # Find countries where this visa provides accessible access
            visa_countries = set()
            for country in G.successors(visa):
                access_type = G[visa][country]['access_type']
                if access_type != "visa_required":
                    visa_countries.add(country)
            current_coverage = visa_countries & uncovered
            if len(current_coverage) > len(covered):
                best_visa = visa
                covered = current_coverage
        if not best_visa:
            # No further coverage possible; break to avoid infinite loop
            break
        selected_visas.add(best_visa)
        uncovered -= covered
        visas.remove(best_visa)  # Remove selected visa to prevent re-selection

    # Check if all countries are covered
    if uncovered:
        display_warning(f"Unable to cover the following countries with the current set of documents: {uncovered}")
    return selected_visas

def find_min_visas_to_cover_all_with_min_access(min_access_level=1):
    """
    Find the minimum set of visas required to cover all countries with at least the specified access level.
    min_access_level: integer representing the minimum access level (1: visa_required, 2: evisa_on_arrival, etc.)
    """
    all_countries = set(visa_data.keys())
    # Exclude passports from being selected as visas
    visas = [doc for doc in G.nodes if G.nodes[doc]['type'] == 'document' and G.nodes[doc]['category'] == 'visa']
    # Include residence permits as they are similar to visas in access
    residence_permits = [doc for doc in G.nodes if G.nodes[doc]['type'] == 'document' and G.nodes[doc]['category'] == 'residence_permit']
    visas.extend(residence_permits)
    
    uncovered = set(all_countries)
    selected_visas = set()

    while uncovered:
        best_visa = None
        covered = set()
        for visa in visas:
            # Find countries where this visa provides at least the min_access_level
            visa_countries = set()
            for country in G.successors(visa):
                access_type = G[visa][country]['access_type']
                if access_hierarchy.get(access_type, 0) >= min_access_level:
                    visa_countries.add(country)
            current_coverage = visa_countries & uncovered
            if len(current_coverage) > len(covered):
                best_visa = visa
                covered = current_coverage
        if not best_visa:
            break
        selected_visas.add(best_visa)
        uncovered -= covered
        visas.remove(best_visa)  # Remove selected visa to prevent re-selection

    if uncovered:
        display_warning(f"Unable to cover the following countries with the current set of documents: {uncovered}")
    return selected_visas

def most_countries_with_x_visas(x):
    """
    Find the combination of x visas that covers the most accessible countries,
    excluding 'visa_required' access types and passports.
    """
    # Exclude passports from being selected as visas
    visas = [doc for doc in G.nodes if G.nodes[doc]['type'] == 'document' and G.nodes[doc]['category'] == 'visa']
    # Include residence permits as they are similar to visas in access
    residence_permits = [doc for doc in G.nodes if G.nodes[doc]['type'] == 'document' and G.nodes[doc]['category'] == 'residence_permit']
    visas.extend(residence_permits)
    
    max_countries = set()
    best_combo = set()

    # Iterate through all combinations of visas of size x
    for combo in combinations(visas, x):
        accessible = set(list_accessible_countries(combo).keys())
        if len(accessible) > len(max_countries):
            max_countries = accessible
            best_combo = set(combo)

    return best_combo, len(max_countries)

def accessible_countries_from_documents(documents):
    """
    Given a set of documents, return a summary of accessible tiers and a detailed list of accessible countries.
    """
    accessible = get_accessible_countries(documents)
    summary = summarize_access(documents)
    return summary, accessible

def best_visa_for_specific_country(target_country):
    """
    Find the best single visa to visit the target country.
    The best visa is defined as the one that provides the highest access level
    to the target country and also grants access to the most other countries.
    Returns the visa, its access type, and additional benefits.
    """
    best_visa, access_type, additional_countries = find_best_visa_for_country(target_country)
    return best_visa, access_type, additional_countries

def suggest_next_best_document(current_documents, target_country=None):
    """
    Suggest the next best document to obtain based on the current set of documents.
    Optionally, ensure the suggested document provides access to a specific target country.
    
    Returns a ranked list of suggested documents with their benefits.
    """
    # All possible documents excluding already owned ones
    all_documents = set([doc for doc in G.nodes if G.nodes[doc]['type'] == 'document'])
    owned_documents = set(current_documents)
    possible_documents = all_documents - owned_documents

    suggestions = []

    for doc in possible_documents:
        # Only suggest visas and residence permits, not passports
        if G.nodes[doc]['category'] not in ['visa', 'residence_permit']:
            continue

        # Calculate additional access this document provides
        additional_access = set()
        for country in G.successors(doc):
            access_type = G[doc][country]['access_type']
            if access_type != "visa_required":
                additional_access.add(country)
        
        # If a target country is specified, check if this document provides access to it
        if target_country:
            provides_target = target_country in additional_access
            if not provides_target:
                continue  # Skip documents that don't provide access to the target country
        else:
            provides_target = False

        # Calculate benefit: number of additional countries
        benefit = len(additional_access)
        # Calculate weighted benefit based on access tiers
        weighted_benefit = sum([access_hierarchy[G[doc][country]['access_type']] for country in additional_access])
        # Count how many new countries this document would add
        suggestions.append({
            'document': doc,
            'additional_countries': benefit,
            'weighted_benefit': weighted_benefit,
            'provides_target': provides_target
        })

    # Sort suggestions based on:
    # 1. Whether it provides access to the target country (if specified)
    # 2. Weighted benefit
    # 3. Number of additional countries
    suggestions_sorted = sorted(
        suggestions,
        key=lambda x: (
            not x['provides_target'],  # Documents providing target access come first
            -x['weighted_benefit'],    # Higher weighted benefit first
            -x['additional_countries'] # More countries first
        )
    )

    return suggestions_sorted

def rank_documents(existing_documents, target_country=None):
    """
    Rank the possible new documents based on how much they benefit the user.
    """
    suggestions = suggest_next_best_document(existing_documents, target_country)
    ranked_list = []
    for idx, suggestion in enumerate(suggestions, start=1):
        ranked_list.append({
            'rank': idx,
            'document': suggestion['document'],
            'additional_countries': suggestion['additional_countries'],
            'weighted_benefit': suggestion['weighted_benefit'],
            'provides_target': suggestion['provides_target']
        })
    return ranked_list

def display_suggestions(ranked_list):
    """
    Display the ranked list of suggested documents in a formatted table.
    """
    if not ranked_list:
        console.print("[bold red]No suggestions available based on the current constraints.[/bold red]")
        return

    table = Table(title="Suggested Next Best Documents")

    table.add_column("Rank", style="cyan", justify="center")
    table.add_column("Document", style="magenta")
    table.add_column("Additional Countries", style="green", justify="center")
    table.add_column("Weighted Benefit", style="yellow", justify="center")
    table.add_column("Provides Target", style="red", justify="center")

    for item in ranked_list:
        rank = str(item['rank'])
        doc = item['document']
        add_countries = str(item['additional_countries'])
        weighted = str(item['weighted_benefit'])
        provides = "Yes" if item['provides_target'] else "No"
        table.add_row(rank, doc, add_countries, weighted, provides)

    console.print(table)

def display_summary(summary):
    """
    Display the summary of access in a formatted table.
    """
    table = Table(title="Summary of Access", show_header=True, header_style="bold blue")

    table.add_column("Access Type", style="dim")
    table.add_column("Number of Countries", justify="right")

    for access_type, count in summary.items():
        if access_type == "freedom_of_movement":
            display_type = "[bold green]Freedom of Movement[/bold green]"
        elif access_type == "visa_free":
            display_type = "[bold yellow]Visa Free[/bold yellow]"
        elif access_type == "evisa_on_arrival":
            display_type = "[bold magenta]eVisa/On Arrival[/bold magenta]"
        else:
            display_type = access_type.capitalize()
        table.add_row(display_type, str(count))

    console.print(table)

def display_accessible_countries(accessible):
    """
    Display the list of accessible countries with their access types in a formatted table.
    """
    table = Table(title="Accessible Countries", show_header=True, header_style="bold blue")

    table.add_column("Country", style="cyan")
    table.add_column("Access Type", style="magenta")

    for country, data in accessible.items():
        access = data['access_type']
        if access == "freedom_of_movement":
            display_access = "[bold green]Freedom of Movement[/bold green]"
        elif access == "visa_free":
            display_access = "[bold yellow]Visa Free[/bold yellow]"
        elif access == "evisa_on_arrival":
            display_access = "[bold magenta]eVisa/On Arrival[/bold magenta]"
        else:
            display_access = access.capitalize()
        table.add_row(country, display_access)

    console.print(table)

def display_best_combination(combo, num_countries):
    """
    Display the best combination of visas covering the most countries.
    """
    table = Table(title="Best Combination of Visas", show_header=True, header_style="bold blue")

    table.add_column("Documents", style="magenta")
    table.add_column("Number of Accessible Countries", justify="right", style="green")

    combo_str = ", ".join(combo)
    table.add_row(combo_str, str(num_countries))

    console.print(table)

def display_min_visas(min_visas, total_countries, access_level=None):
    """
    Display the minimum visas required to cover all countries.
    """
    if access_level:
        title = f"Minimum Visas to Cover All Countries with at Least '{access_level.replace('_', ' ').title()}' Access"
    else:
        title = "Minimum Visas to Cover All Countries"

    table = Table(title=title, show_header=True, header_style="bold blue")

    table.add_column("Documents", style="magenta")
    table.add_column("Number of Accessible Countries", justify="right", style="green")

    combo_str = ", ".join(min_visas)
    table.add_row(combo_str, str(total_countries))

    console.print(table)

def display_best_visa(best_visa, access_type, additional_countries, target_country):
    """
    Display the best visa to visit a specific country along with its benefits.
    """
    table = Table(title=f"Best Visa to Visit {target_country}", show_header=True, header_style="bold blue")

    table.add_column("Document", style="magenta")
    table.add_column("Access Type", style="green")
    table.add_column("Additional Countries Covered", style="yellow")

    if best_visa:
        additional = ", ".join(additional_countries) if additional_countries else "None"
        table.add_row(best_visa, access_type.replace('_', ' ').capitalize(), additional)
    else:
        table.add_row("N/A", "N/A", "N/A")

    console.print(table)

def display_warning(message):
    """
    Display a warning message.
    """
    console.print(f"[bold red]Warning:[/bold red] {message}")

if __name__ == "__main__":
    # Example 1: Accessible countries with Indian Passport, US Visa, and Schengen Visa
    visas = ["Indian Passport", "US Visa", "Schengen Visa"]
    summary, accessible = accessible_countries_from_documents(visas)
    console.print("\n[bold underline]Example 1: Accessible Countries with " + str(visas) + "[/bold underline]")
    display_summary(summary)
    display_accessible_countries(accessible)

    # Example 2: Best visa to visit Mexico
    target_country = "Mexico"
    best_visa, access_type, additional_countries = best_visa_for_specific_country(target_country)
    console.print(f"\n[bold underline]Example 2: Best Visa to Visit {target_country}[/bold underline]")
    display_best_visa(best_visa, access_type, additional_countries, target_country)

    # Example 3: Best combination of 3 visas covering most countries
    x = 3
    best_combo, num_countries = most_countries_with_x_visas(x)
    console.print(f"\n[bold underline]Example 3: Best Combination of {x} Visas Covering Most Countries[/bold underline]")
    display_best_combination(best_combo, num_countries)

    # Example 4: Minimum visas to cover all countries
    min_visas = find_min_visas_to_cover_all()
    accessible_min, _ = accessible_countries_from_documents(min_visas)
    console.print(f"\n[bold underline]Example 4: Minimum Visas to Cover All Countries[/bold underline]")
    display_min_visas(min_visas, sum(accessible_min.values()))

    # Example 5: Minimum visas to cover all countries with at least 'visa_free' access
    min_access_level = access_hierarchy["visa_free"]
    min_visas_free = find_min_visas_to_cover_all_with_min_access(min_access_level)
    accessible_min_free, _ = accessible_countries_from_documents(min_visas_free)
    access_level_name = [k for k, v in access_hierarchy.items() if v == min_access_level][0]
    console.print(f"\n[bold underline]Example 5: Minimum Visas to Cover All Countries with at Least '{access_level_name.replace('_', ' ').title()}' Access[/bold underline]")
    display_min_visas(min_visas_free, sum(accessible_min_free.values()), access_level=access_level_name)

    # Example 6: Suggest Next Best Document (No Constraint)
    current_documents = ["Indian Passport"]
    console.print(f"\n[bold underline]Example 6: Suggest Next Best Document (No Constraint)[/bold underline]")
    ranked_suggestions = rank_documents(existing_documents=current_documents, target_country=None)
    display_suggestions(ranked_suggestions)

    # Example 7: Suggest Next Best Document with Constraint (Must Provide Access to Mexico)
    console.print(f"\n[bold underline]Example 7: Suggest Next Best Document (Must Provide Access to Mexico)[/bold underline]")
    ranked_suggestions_mexico = rank_documents(existing_documents=current_documents, target_country="Mexico")
    display_suggestions(ranked_suggestions_mexico)

    # Example 8: Suggesting multiple next best documents sequentially
    console.print(f"\n[bold underline]Example 8: Sequential Suggestions to Strengthen Passport[/bold underline]")
    # Starting with Indian Passport
    current_docs = set(["Indian Passport"])
    steps = 3  # Number of suggestions to make
    for step in range(1, steps + 1):
        console.print(f"\n[bold green]Step {step}:[/bold green] Current Documents: {', '.join(current_docs)}")
        suggestions = suggest_next_best_document(current_docs)
        if not suggestions:
            console.print("[bold red]No more documents to suggest.[/bold red]")
            break
        # Take the top suggestion
        top_suggestion = suggestions[0]
        next_doc = top_suggestion['document']
        benefit = top_suggestion['weighted_benefit']
        provides_target = top_suggestion['provides_target']
        console.print(f"Suggested Next Document: [bold magenta]{next_doc}[/bold magenta] (Benefit: {benefit}, Provides Target: {'Yes' if provides_target else 'No'})")
        current_docs.add(next_doc)
