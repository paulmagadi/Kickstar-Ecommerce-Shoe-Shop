$(document).ready(function () {
    $(document).off('click', '.add-to-cart').on('click', '.add-to-cart', function(e) {
        e.preventDefault();

        var productId = $(this).val(); // Get product ID from button
        const csrfToken = $('meta[name="csrf-token"]').attr('content');
        const cartAddUrl = $('meta[name="cart-add-url"]').attr('content');

        var quantityElement = $(this).closest('.product-page-product-details').find('.quantity');
        var productQty = parseInt(quantityElement.text().trim()) || 1;


        $.ajax({
            type: 'POST',
            url: cartAddUrl,
            data: {
                product_id: productId,
                product_qty: productQty,
                csrfmiddlewaretoken: csrfToken,
                action: 'post'
            },
            success: function(json){
                $('.cart-count').text(json.qty); 
                location.reload(); 
            },
            error: function(xhr, errmsg, err){
                console.error("Error adding to cart:", errmsg);
            }
        });

        return false; // Prevent default form submission
    });
});


$(document).on('click', '.add-quantity', function(e){
    e.preventDefault();
    var $button = $(this);
    var productId = $button.data('index');
    var quantityElement = $('.item-quantity[data-index="' + productId + '"]');
    var productQty = parseInt(quantityElement.text().trim()) || 0;
    productQty += 1;

    const csrfToken = $('meta[name="csrf-token"]').attr('content');
    const cartAddUrl = $('meta[name="cart_update-url"]').attr('content');

    var stockQuantity = parseInt(quantityElement.data('stock')); 

    if (productQty > stockQuantity) {
        $button.prop('disabled', true)
            .css('cursor', 'not-allowed')
            .attr('title', `Maximum stock quantity of ${stockQuantity} reached`);
        return;
    }
    
    $.ajax({
        type: 'POST',
        url: cartAddUrl,
        data: {
            product_id: productId,
            product_qty: productQty,
            csrfmiddlewaretoken: csrfToken,
            action: 'post'
        },
        success: function(json){
            location.reload();
        },
        error: function(xhr, errmsg, err){
            // Handle error
        }
    });
});


$(document).on('click', '.reduce-quantity', function(e){
    e.preventDefault();
    var $button = $(this);
    var productId = $button.data('index');
    var quantityElement = $('.item-quantity[data-index="' + productId + '"]');
    var productQty = parseInt(quantityElement.text()) - 1;

    const csrfToken = $('meta[name="csrf-token"]').attr('content');
    const cartAddUrl = $('meta[name="cart_update-url"]').attr('content');
    
    if (productQty < 1) {
        $button.prop('disabled', true)
        .css('cursor', 'not-allowed')
        .attr('title', 'You need atleast one item');
        return;  
    }
    $.ajax({
        type: 'POST',
        url: cartAddUrl,
        data: {
            product_id: productId,
            product_qty: productQty,
            csrfmiddlewaretoken: csrfToken,
            action: 'post'
        },
        success: function(json){
            location.reload();
        },
        error: function(xhr, errmsg, err){
            // Handle error
        }
    });
});



$(document).on('click', '.remove-item', function(e){
    e.preventDefault();
    var productId = $(this).data('index');
    var itemRow = $(this).closest('.cart-element'); 

    const csrfToken = $('meta[name="csrf-token"]').attr('content');
    const cartDeleteUrl = $('meta[name="cart_delete-url"]').attr('content');
    
    $.ajax({
        type: 'POST',
        url: cartDeleteUrl,
        data: {
            product_id: productId,
            csrfmiddlewaretoken: csrfToken,
            action: 'post'
        },
        success: function(json){
            itemRow.fadeOut(500, function () { $(this).remove(); }); 
            location.reload();
        },
        error: function(xhr, errmsg, err){
            // Handle error
        }
    });
});

