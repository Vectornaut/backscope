#!/bin/bash

# --- classify requirements ---

not_installed=()
not_required=()
indirectly_required=()
directly_required=()

padding="                        "

for dep in $(cat requirements-freeze.txt); do
  pkg=${dep%==*}
  details=$(pip show $pkg 2> /dev/null)
  if [ -z "$details" ]; then
    not_installed+=( $pkg )
  else
    # hat tip Anton Korneychuk (https://stackoverflow.com/a/69022922)
    if grep -q "^$pkg\s*\(#\|$\)" requirements.txt; then
      # explicitly required
      directly_required+=( $pkg )
    else
      # not explicitly required
      parents_line=$(echo "$details" | grep Required-by)
      parents=${parents_line#"Required-by: "}
      if [ "$parents" ]; then
        # required by another package
        indirectly_required+=( "$pkg${padding:0:$((${#padding} - ${#pkg}))}$parents" )
      else
        # not required by another package
        not_required+=( $pkg )
      fi
    fi
  fi
done

# --- list requirements ---

catcolor=1
if [[ -z "${not_installed[@]}" ]]; then
  tput bold setaf 8; echo "✓ All frozen packages are installed"; tput sgr0
else
  tput setaf $catcolor; echo -n ╭; tput bold; echo " Not installed"; tput sgr0
  for pkg in "${not_installed[@]}"; do
    tput setaf 1; echo -n │; tput sgr0
    echo "   $pkg"
  done
fi

catcolor=3
if [[ -z "${not_required[@]}" ]]; then
  tput bold setaf 8; echo "✓ All installed frozen packages are required"; tput sgr0
else
  tput setaf $catcolor; echo -n ╭; tput bold; echo " Not required"; tput sgr0
  for pkg in "${not_required[@]}"; do
    tput setaf $catcolor; echo -n │; tput sgr0
    tput sgr0; echo "   $pkg"; tput setaf 3
  done
fi

catcolor=2
if [[ -z "${indirectly_required[@]}" ]]; then
  tput bold setaf 8; echo "  No installed frozen packages are indirectly required"; tput sgr0
else
  tput setaf $catcolor; echo -n ╭; tput bold; echo -n " Indirectly required"
  tput sgr0; tput setaf $catcolor; echo -n " ⋅⋅⋅⋅⋅ "; tput bold; echo "by"; tput sgr0
  for pkg in "${indirectly_required[@]}"; do
    tput setaf 2; echo -n │; tput sgr0
    tput sgr0; echo "   $pkg"; tput setaf 2
  done
fi

catcolor=4
if [[ -z "${directly_required[@]}" ]]; then
  tput bold setaf 5; echo "▴ No installed frozen packages are directly required"; tput sgr0
else
  tput setaf $catcolor; echo -n ╭; tput bold; echo " Directly required"; tput sgr0
  for pkg in "${directly_required[@]}"; do
    tput setaf $catcolor; echo -n │; tput sgr0
    tput sgr0; echo "   $pkg"; tput setaf 4
  done
fi

# reset terminal style to default
tput sgr0
