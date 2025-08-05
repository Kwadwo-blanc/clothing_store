// main.js - Basic interactivity for cart and checkout

document.addEventListener("DOMContentLoaded", function () {
  const cart = [];

  function addToCart(productId, productName, price) {
    cart.push({ productId, productName, price });
    alert(`${productName} added to cart!`);
    updateCartDisplay();
  }

  function updateCartDisplay() {
    const cartList = document.getElementById("cart-list");
    if (!cartList) return;
    cartList.innerHTML = "";
    cart.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.productName} - $${item.price}`;
      cartList.appendChild(li);
    });
  }

  window.addToCart = addToCart;
});
