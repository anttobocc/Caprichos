# 🧁 Caprichos

### E-commerce gastronómico | Django · Python · JavaScript

---

## 👩‍💻 About the Project

**Caprichos.Store.Ctes** es una aplicación web e-commerce desarrollada para **Capricho — Boutique Empanadas & Bakery**, un emprendimiento gastronómico.

El proyecto fue desarrollado con **Django** y está orientado a la gestión de productos, categorías, variantes, combos, pedidos y usuarios, ofreciendo una experiencia de compra adaptada tanto a dispositivos de escritorio como a dispositivos móviles.

La aplicación busca digitalizar el proceso de compra del negocio, desde la consulta del catálogo hasta la preparación y confirmación del pedido mediante WhatsApp.

---

## 🚀 Currently

- 🧁 Desarrollando un e-commerce para un emprendimiento gastronómico.
- 📦 Gestionando productos, categorías y variantes.
- 🎁 Implementando combos promocionales.
- 🛒 Desarrollando el carrito de compras.
- 📅 Implementando selección de fecha para los pedidos.
- 🚚 Trabajando con pedidos para retiro o envío.
- 📱 Integrando la confirmación de pedidos mediante WhatsApp.
- ⚙️ Desarrollando un panel de administración personalizado.
- 📱 Adaptando la interfaz para dispositivos móviles.
- 🖼️ Gestionando imágenes y recursos del catálogo.

---

## 🛠️ Languages and Tools

### Languages

![Languages](https://skillicons.dev/icons?i=python,js)

### Web Development

![Web Development](https://skillicons.dev/icons?i=html,css,django)

### Database

![Database](https://skillicons.dev/icons?i=sqlite)

### Tools

![Tools](https://skillicons.dev/icons?i=git,github,vscode)

---

## 📋 Main Features

### 🛍️ Product Catalog

El sistema cuenta con un catálogo organizado para facilitar la consulta de los productos.

- Productos organizados por categorías.
- Diferentes variantes y presentaciones.
- Productos destacados.
- Combos promocionales.
- Control de disponibilidad.
- Control de visibilidad.
- Gestión de imágenes.
- Información y precios de los productos.

---

### 🎁 Promotional Combos

El sistema permite crear combos promocionales compuestos por diferentes productos del catálogo.

Cada combo puede definir:

- Productos incluidos.
- Cantidad de cada producto.
- Precio promocional.
- Imagen.
- Descripción.
- Disponibilidad.

Los combos forman parte del catálogo y pueden agregarse al carrito como cualquier otro producto.

---

### 🛒 Shopping Cart

El carrito permite al cliente preparar su pedido antes de confirmarlo.

- Agregar productos.
- Seleccionar variantes.
- Modificar cantidades.
- Eliminar productos.
- Visualizar el contenido del carrito.
- Calcular el total del pedido.

---

### 📅 Checkout

El proceso de checkout permite especificar la información necesaria para realizar el pedido.

El cliente puede seleccionar:

- Tipo de entrega.
- Retiro en el local.
- Envío.
- Dirección de envío.
- Fecha deseada.
- Observaciones.

El sistema aplica las reglas de negocio correspondientes antes de confirmar el pedido.

---

### 📱 WhatsApp Orders

Una vez preparado el pedido, el sistema permite generar la información necesaria para enviarla mediante **WhatsApp**.

Esto facilita la comunicación entre el cliente y el emprendimiento para coordinar la compra.

---

### ⚙️ Administration Panel

El proyecto cuenta con un panel de administración personalizado para gestionar el funcionamiento de la tienda.

Desde el panel se pueden administrar:

- Productos.
- Categorías.
- Variantes.
- Combos.
- Pedidos.
- Usuarios.
- Configuración del negocio.
- Disponibilidad de productos.
- Visibilidad del catálogo.

---

## 👥 User Management

El sistema utiliza el sistema de autenticación de Django para gestionar los usuarios y sus permisos.

Permite trabajar con diferentes niveles de acceso según las necesidades de administración del sistema.

---

## 📦 Order Management

Los pedidos almacenan la información necesaria para conservar el historial de cada compra.

Cada pedido puede contener:

- Datos del cliente.
- Productos seleccionados.
- Variantes.
- Cantidades.
- Precios.
- Tipo de entrega.
- Dirección de envío.
- Fecha solicitada.
- Observaciones.
- Estado del pedido.

Los datos relevantes de los productos y precios utilizados se conservan en el pedido para evitar que modificaciones posteriores del catálogo alteren la información histórica de una compra.

---

## 📱 Responsive Design

La interfaz fue desarrollada teniendo en cuenta diferentes tamaños de pantalla.

El diseño se adapta a:

- 🖥️ Desktop.
- 💻 Laptop.
- 📱 Mobile.

La versión móvil utiliza estructuras y componentes adaptados para facilitar la navegación por el catálogo, la selección de productos y el proceso de compra desde pantallas pequeñas.

---

## 📐 Business Rules

El sistema contempla diferentes reglas relacionadas con la gestión de pedidos:

- Los pedidos requieren un mínimo de **1 día de anticipación**.
- Se pueden seleccionar fechas de hasta **10 días de anticipación**.
- Los pedidos pueden realizarse para retiro en el local o mediante envío.
- Los productos pueden configurarse como disponibles o no disponibles.
- Los productos y categorías pueden mostrarse u ocultarse según su configuración.

---

## ✅ Validations

El sistema incorpora validaciones en el backend y en los formularios para controlar:

- Datos de los clientes.
- Cantidades de productos.
- Variantes.
- Fechas de pedido.
- Tipo de entrega.
- Disponibilidad de productos.
- Reglas específicas del negocio.

---

## 🏗️ Project Architecture

El proyecto se encuentra organizado en diferentes aplicaciones según las responsabilidades del sistema:

```text
Caprichos.Store.Ctes/
│
├── catalogo/       → Productos, categorías, variantes y combos
├── pedidos/        → Carrito y gestión de pedidos
├── panel/          → Administración del negocio
├── usuarios/       → Gestión de usuarios
├── config/         → Configuración general del proyecto
│
├── templates/      → Interfaces HTML
├── static/         → CSS, JavaScript y recursos estáticos
├── media/          → Imágenes y archivos multimedia
│
├── manage.py
└── README.md
