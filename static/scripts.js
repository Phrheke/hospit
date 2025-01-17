document.addEventListener('DOMContentLoaded', function () {
    const mapContainer = document.getElementById('map');
    const hospitalList = document.getElementById('hospital-list');
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');

    let currentLat = null;
    let currentLng = null;

    // Initialize HERE Maps
    function initializeMap(lat = 37.7749, lng = -122.4194) {
        const platform = new H.service.Platform({
            apikey: "AnNqHPQq1CjIAlhwXf7m0OiN54e8hOD43y7u0v1dYuY",
        });

        const defaultLayers = platform.createDefaultLayers();

        // Clear existing map content
        mapContainer.innerHTML = '';

        // Create a new map instance
        const map = new H.Map(mapContainer, defaultLayers.vector.normal.map, {
            center: { lat: lat, lng: lng },
            zoom: 14,
            pixelRatio: window.devicePixelRatio || 1,
        });

        const behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(map));
        const ui = H.ui.UI.createDefault(map, defaultLayers);

        console.log("Map initialized successfully.");
        return { map, ui };
    }

    // Function to geocode an address or coordinates
    function geocodeLocation(location) {
        const platform = new H.service.Platform({
            apikey: "AnNqHPQq1CjIAlhwXf7m0OiN54e8hOD43y7u0v1dYuY",
        });

        const geocoder = platform.getSearchService();

        return new Promise((resolve, reject) => {
            // Ensure location is a valid string
            if (!location || typeof location !== 'string') {
                reject('Invalid location input.');
                return;
            }

            // Use the 'q' parameter for the geocode query
            geocoder.geocode({ q: location }, (result) => {
                if (result.items.length > 0) {
                    const { lat, lng } = result.items[0].position;
                    resolve({ lat, lng });
                } else {
                    reject('Location not found');
                }
            }, (error) => {
                reject(error);
            });
        });
    }

    // Function to get user geolocation
    function getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                const { latitude, longitude } = position.coords;
                currentLat = latitude;
                currentLng = longitude;

                // Initialize map centered on user location
                const { map, ui } = initializeMap(latitude, longitude);

                // Add a marker for user location with a custom icon
                const userIcon = new H.map.Icon(
                    'https://img.icons8.com/color/48/000000/user-location.png' // Example icon URL
                );
                const userMarker = new H.map.Marker(
                    { lat: latitude, lng: longitude },
                    { icon: userIcon }
                );
                map.addObject(userMarker);
                console.log("User location marker added.");

                // Fetch hospitals and add markers
                fetchHospitals(latitude, longitude, map, ui);
            }, 
            (error) => {
                alert('Unable to retrieve location. Ensure location services are enabled.');
                console.error("Geolocation error:", error);
            });
        } else {
            alert('Geolocation is not supported by this browser.');
        }
    }

    // Fetch hospitals based on location
    function fetchHospitals(lat, lng, map, ui) {
        fetch('/api/search_hospitals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ latitude: lat, longitude: lng }),
        })
            .then((response) => response.json())
            .then((data) => {
                console.log("Fetched hospital data:", data);

                // Clear the list before adding new data
                hospitalList.innerHTML = '';

                // Ensure data is valid and non-empty
                if (data && Array.isArray(data) && data.length > 0) {
                    data.forEach((hospital) => {
                        const li = document.createElement('li');
                        li.textContent = hospital.title;
                        hospitalList.appendChild(li);

                        // Validate the hospital location data
                        if (hospital.position && hospital.position.lat && hospital.position.lng) {
                            const hospitalMarker = new H.map.Marker({
                                lat: hospital.position.lat,
                                lng: hospital.position.lng,
                            });

                            // Add marker to the map
                            map.addObject(hospitalMarker);
                            console.log(`Marker added for ${hospital.title}`);

                           
                        } else {
                            console.warn(`Invalid position data for hospital: ${hospital.title}`);
                        }
                    });
                } else {
                    console.warn("No hospital data available or invalid data.");
                }
            })
            .catch((err) => {
                console.error("Error fetching hospitals:", err);
            });
    }

    // Search button click event
    searchButton.addEventListener('click', () => {
        const location = searchInput.value.trim();

        if (location) {
            // Geocode the location entered by the user
            geocodeLocation(location)
                .then(({ lat, lng }) => {
                    // Initialize map with the new location
                    const { map, ui } = initializeMap(lat, lng);

                    // Add a marker for user location with a custom icon
                    const userIcon = new H.map.Icon(
                        'https://img.icons8.com/color/48/000000/user-location.png' // Example icon URL
                    );
                    const userMarker = new H.map.Marker(
                        { lat, lng },
                        { icon: userIcon }
                    );
                    map.addObject(userMarker);
                    console.log("User location marker added.");

                    // Fetch hospitals based on the new location
                    fetchHospitals(lat, lng, map, ui);
                })
                .catch((error) => {
                    alert('Error: ' + error);
                    console.error(error);
                });
        } else {
            alert('Please enter a location to search.');
        }
    });

    // Load user's geolocation by default
    getUserLocation();
});
