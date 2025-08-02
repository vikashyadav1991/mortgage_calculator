#!/bin/bash

# Simple deployment script for render.com

echo "Preparing for deployment..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git and try again."
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Check if remote exists
if ! git remote | grep -q "render"; then
    echo "Please enter your Render Git repository URL:"
    read render_url
    git remote add render "$render_url"
fi

# Push to render
echo "Pushing to Render..."
git push -u render master

echo "Deployment complete! Your app should be live soon."
echo "Check your Render dashboard for deployment status."