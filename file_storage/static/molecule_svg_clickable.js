var svgObject = document.getElementById("svgContent");

function extractAtomCoords(svgElement) {
    const paths = svgElement.selectAll('path');
    const atoms = {};
    const bonds = new Set();
    const used_letters = new Set();

    paths.each(function() {
        const path = d3.select(this);
        const classAttr = path.attr('class');
        const dAttr = path.attr('d');

        if (!classAttr || !dAttr) {
            // Skip if either attribute is missing.
            return;
        }

        const classNames = classAttr.split(' ');
        const class_1 = classNames[0];
        const class_2 = classNames[1];
        const class_3 = classNames[2];

        const coords = dAttr.split('L').map(coordPart => {
            const coord = coordPart.split(' ')[1];
            return coord.split(',').map(parseFloat);
        });

        // Handle special case where class is of the form 'atom-*'
        if (classNames.length === 1 && class_1.startsWith('atom-')) {

            // Check if the letter has already been used.
            if (!used_letters.has(class_1[5])) {
                used_letters.add(class_1[5]);
                const avgCoords = processCoordinates(dAttr)
                atoms[class_1] = avgCoords;

                return;  // Continue to the next path.
            }
        }

        if (!bonds.has(class_1)) {
            if (class_2 && !atoms[class_2]) atoms[class_2] = coords[0];
            if (class_3 && !atoms[class_3]) atoms[class_3] = coords[1];
            bonds.add(class_1);
        }
    });

    return atoms;
}

function processCoordinates(dAttr) {
    const coordRegex = /([0-9\.]+)\s+([0-9\.]+)/g;
    let match;
    let xCoords = [];
    let yCoords = [];

    // Extract all pairs of coordinates
    while ((match = coordRegex.exec(dAttr)) !== null) {
        xCoords.push(parseFloat(match[1]));
        yCoords.push(parseFloat(match[2]));
    }

    // Find the maximum and minimum of each coordinate
    let [minX, maxX] = [Math.min(...xCoords), Math.max(...xCoords)];
    let [minY, maxY] = [Math.min(...yCoords), Math.max(...yCoords)];

    // Calculate and return the average of the max and min for each coordinate
    return [(minX + maxX) / 2, (minY + maxY) / 2];
}

function plotAtomCoords(atomCoords) {
    const svgObject = document.getElementById("svgContent");
    const svgContainer = d3.select(svgObject.contentDocument.documentElement);

    // Convert atomCoords to an array of objects that contain both coordinates and keys
    const atomsArray = Object.keys(atomCoords).map(key => ({
        key: key,
        coords: atomCoords[key]
    }));
    
    const voronoi = d3.voronoi().extent([[-1, -1], [1001, 1001]]); // Define the Voronoi generator with an appropriate extent
    const voronoiDiagram = voronoi(atomsArray.map(atom => atom.coords)); // Generate the Voronoi diagram based on the coordinates only

    const cell = svgContainer.append("g")
        .selectAll(".cell")
        .data(voronoiDiagram.polygons())
        .enter().append("g").attr("class", "cell");

    // Store circle elements in an object, using the atom IDs as keys.
    const circleElements = {};

    // Append circles
    for (let atom of atomsArray) {
        let circle = svgContainer.append("circle")
            .attr("cx", atom.coords[0])
            .attr("cy", atom.coords[1])
            .attr("r", 10)  // radius of circle
            .style("fill", "none");
        circleElements[atom.key] = circle;
    }

    // Append Voronoi paths (cells)
    cell.append("path")
        .attr("d", function(d) { return d ? "M" + d.join("L") + "Z" : null; })
        .style("fill", "none")  // set fill color
        .style("opacity", 0.4)  // set transparency, 0 fully transparent, 1 fully opaque
        .style("pointer-events", "all")
        .style("stroke", "none") // add stroke (line around the cell)
        .style("stroke-width", "1px") // adjust stroke width as needed
        .on("click", function(d, i) {
            console.log("Clicked on atom: ", atomsArray[i].key);
        })
        .on("mouseover", function(d, i) {
            // select the atom point
            let atomPoint = circleElements[atomsArray[i].key];
            console.log("Mouseover atom point: ", atomPoint);
            // change the color of the atom point
            atomPoint.style("fill", "red");
        })
        .on("mouseout", function(d, i) {
            // select the atom point
            let atomPoint = circleElements[atomsArray[i].key];
            console.log("Mouseout atom point: ", atomPoint);
            // change the color back to the original
            atomPoint.style("fill", "none");
        });
}

window.onload = function() {
    var svgDoc = svgObject.contentDocument;  // Get the document of the SVG content
    var d3SVG = d3.select(svgDoc.documentElement);  // Create a D3 selection from the SVG root element
    const atomCoords = extractAtomCoords(d3SVG);
    plotAtomCoords(atomCoords);
    console.log(atomCoords);
};