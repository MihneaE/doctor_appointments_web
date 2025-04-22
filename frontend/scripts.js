// Update apiUrl if needed (e.g., "http://localhost:8000/api/v1/medical-specialities/")
const apiUrl = "http://localhost:5555/api/v1/medical-specialities/";

// Fetch specialties (GET)
function fetchSpecialties() {
  $.get(apiUrl, function(data) {
    $("#specialtyItems").empty();
    data.forEach((specialty) => {
      $("#specialtyItems").append(`
        <li
          class="list-group-item d-flex justify-content-between align-items-center"
          data-id="${specialty.id}"
        >
          <div>
            <strong>${specialty.name}</strong>
            <p class="mb-1">${specialty.description}</p>
          </div>
          <div>
            <button class="btn btn-warning btn-sm edit-btn">Edit</button>
            <button class="btn btn-danger btn-sm delete-btn">Delete</button>
          </div>
        </li>
      `);
    });
  }).fail(function(error) {
    console.error("Error fetching specialties:", error);
    alert("Failed to load specialties.");
  });
}

// Add a new specialty (POST)
$("#addSpecialtyBtn").click(function() {
  const name = $("#specialtyInput").val();
  const description = $("#specialtyDescription").val();

  if (!name || !description) {
    alert("Both name and description are required!");
    return;
  }

  $.post(apiUrl, { name, description })
    .done(function() {
      // Clear inputs
      $("#specialtyInput").val("");
      $("#specialtyDescription").val("");
      // Refresh list
      fetchSpecialties();
    })
    .fail(function(error) {
      console.error("Error adding specialty:", error);
      alert("Failed to add specialty.");
    });
});

// Edit specialty (PUT)
$(document).on("click", ".edit-btn", function() {
  const listItem = $(this).closest("li");
  const id = listItem.data("id");
  const currentName = listItem.find("strong").text();
  const currentDescription = listItem.find("p").text();

  const name = prompt("Enter new name:", currentName);
  const description = prompt("Enter new description:", currentDescription);

  if (!name || !description) {
    alert("Both name and description are required!");
    return;
  }

  $.ajax({
    url: `${apiUrl}${id}/`,
    type: "PUT",
    contentType: "application/json",
    data: JSON.stringify({ name, description }),
    success: function() {
      fetchSpecialties();
    },
    error: function(error) {
      console.error("Error updating specialty:", error);
      alert("Failed to update specialty.");
    }
  });
});

// Delete specialty (DELETE)
$(document).on("click", ".delete-btn", function() {
  const id = $(this).closest("li").data("id");

  if (confirm("Are you sure you want to delete this specialty?")) {
    $.ajax({
      url: `${apiUrl}${id}/`,
      type: "DELETE",
      success: function() {
        fetchSpecialties();
      },
      error: function(error) {
        console.error("Error deleting specialty:", error);
        alert("Failed to delete specialty.");
      }
    });
  }
});

// Initial fetch on page load
$(document).ready(function() {
  fetchSpecialties();
});


