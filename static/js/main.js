// static/js/main.js
document.addEventListener('DOMContentLoaded', function(){
  // confirmación visual reducida al enviar formularios de añadir al carrito
  document.querySelectorAll('.add-form').forEach(form=>{
    form.addEventListener('submit', function(e){
      // simple confirm modal estilo nativo
      const cantidad = this.querySelector('input[name="cantidad"]').value;
      if(!confirm(`Añadir ${cantidad} al carrito?`)){
        e.preventDefault();
      }
    });
  });
});
