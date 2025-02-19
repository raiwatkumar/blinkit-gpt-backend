// Add at the beginning of your script.js
function startGPT() {
    // // Show back button
    // document.getElementById('backButton').style.display = 'flex';
    
    // Hide feature box and show search interface
    document.getElementById('featureBox').style.display = 'none';
    document.getElementById('searchInterface').style.display = 'flex';
    
    // Hide marketing content
    const mainContent = document.querySelectorAll('.welcome-banner, .quick-links, .offers-banner');
    mainContent.forEach(element => {
        element.style.display = 'none';
    });
    
    // Show prompt suggestions
    document.getElementById('promptSuggestions').style.display = 'block';
    
    // Focus the search input
    document.getElementById('taskInput').focus();
}

// When page loads
document.addEventListener('DOMContentLoaded', function() {
    // Show welcome overlay
    document.getElementById('welcomeOverlay').style.display = 'flex';
    
    // Hide items display and product container initially
    document.getElementById('itemsDisplay').style.display = 'none';
    document.getElementById('productContainer').style.display = 'none';

    const taskInput = document.getElementById("taskInput");

    // Add click event listener to back button
    document.getElementById('backButton').addEventListener('click', goBack);
});

// Add new function to handle prompt clicks
function usePrompt(prompt) {
    const taskInput = document.getElementById('taskInput');
    // Remove quotes from the prompt
    taskInput.value = prompt.replace(/"/g, '');
    // Hide suggestions
    document.getElementById('promptSuggestions').style.display = 'none';
    // Process the task
    processTask();
}

async function processTask() {
    const taskInput = document.getElementById("taskInput");
    const itemsDisplay = document.getElementById("itemsDisplay");
    const productContainer = document.getElementById("productContainer");
    
    // Don't process empty queries
    if (!taskInput.value.trim()) return;

    // Hide suggestions
    document.getElementById('promptSuggestions').style.display = 'none';
    
    // Show and update items display
    itemsDisplay.style.display = "block";
    itemsDisplay.textContent = "Thinking...";
    itemsDisplay.classList.add('thinking');
    
    // Clear previous products
    productContainer.innerHTML = '';
    productContainer.style.display = "none";

    try {
        const response = await fetch("http://127.0.0.1:8000/process-request/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name: taskInput.value }),
        });

        const data = await response.json();
        
        // Remove thinking animation
        itemsDisplay.classList.remove('thinking');

        if (data.status === "success") {
            // Update items display with task name
            itemsDisplay.textContent = data.task_name;
            
            // Show and populate product container
            productContainer.style.display = "grid";
            
            // Use data.items directly since they're already properly formatted
            data.items.forEach(item => {
                const productCard = createProductCard(item);
                productContainer.appendChild(productCard);
            });
        } else {
            itemsDisplay.textContent = "Error: " + data.message;
            productContainer.style.display = "none";
        }
    } catch (error) {
        itemsDisplay.classList.remove('thinking');
        itemsDisplay.textContent = "Error: " + error.message;
        productContainer.style.display = "none";
    }

    taskInput.value = "";
}

// Initialize cart count
let cartCount = 0;

function createProductCard(item) {
    const card = document.createElement("div");
    card.classList.add("product-card");

    // Add image if URL exists
    if (item.image_url) {
        const image = document.createElement("img");
        image.src = item.image_url;
        image.alt = item.name;
        image.classList.add("product-image");
        card.appendChild(image);
    }

    const name = document.createElement("div");
    name.classList.add("product-name");
    name.textContent = item.name;

    const weight = document.createElement("div");
    weight.classList.add("product-weight");
    weight.textContent = `${item.quantity} ${item.units}`;

    const quantityControls = document.createElement("div");
    quantityControls.classList.add("quantity-controls");

    const decreaseBtn = document.createElement("button");
    decreaseBtn.classList.add("quantity-btn");
    decreaseBtn.textContent = "-";
    
    const quantityDisplay = document.createElement("span");
    quantityDisplay.classList.add("quantity-display");
    quantityDisplay.textContent = "0";  // Start at 0
    
    const increaseBtn = document.createElement("button");
    increaseBtn.classList.add("quantity-btn");
    increaseBtn.textContent = "+";

    // Add event listeners for quantity controls
    let quantity = 0;  // Start at 0
    
    decreaseBtn.addEventListener("click", () => {
        if (quantity > 0) {
            quantity--;
            quantityDisplay.textContent = quantity;
            cartCount--;  // Decrease cart count
            updateCartCount();  // Update cart display
        }
    });

    increaseBtn.addEventListener("click", () => {
        quantity++;
        quantityDisplay.textContent = quantity;
        cartCount++;  // Increase cart count
        updateCartCount();  // Update cart display
        
        // Show add animation
        const button = increaseBtn;
        button.style.backgroundColor = "var(--blinkit-green)";
        button.style.color = "white";
        
        // Reset button after animation
        setTimeout(() => {
            button.style.backgroundColor = "";
            button.style.color = "";
        }, 200);
    });

    quantityControls.appendChild(decreaseBtn);
    quantityControls.appendChild(quantityDisplay);
    quantityControls.appendChild(increaseBtn);

    card.appendChild(name);
    card.appendChild(weight);
    card.appendChild(quantityControls);

    return card;
}

// Update cart count display
function updateCartCount() {
    const cartCountElement = document.getElementById('cartCount');
    if (cartCountElement) {
        cartCountElement.textContent = cartCount;
    }
}

// Add new function to handle back button

// Add function to show cart action button
function displayProducts(products) {
    const productContainer = document.getElementById('productContainer');
    const cartAction = document.getElementById('cartAction');
    
    productContainer.style.display = 'grid';
    cartAction.style.display = 'block';  // Show cart action when products are displayed
    
    // ... rest of displayProducts function ...
}

// Add function to handle adding all items
function addAllToCart() {
    const button = document.querySelector('.cart-action .add-to-cart-btn');
    
    // Show added animation
    button.textContent = "Added to Cart ✓";
    button.style.backgroundColor = "var(--blinkit-green)";
    button.style.color = "white";
    button.disabled = true;
    
    // Reset button after animation
    setTimeout(() => {
        button.textContent = "Add Items to Cart";
        button.style.backgroundColor = "";
        button.style.color = "";
        button.disabled = false;
    }, 1000);
}