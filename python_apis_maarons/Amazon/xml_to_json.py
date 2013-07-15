def toJSON(node):
    def processAttr(attr):
        ret = {}
        i = 0
        while attr is not None and i < attr.length:
            item = attr.item(i)
            ret[item.name] = item.value
            i += 1
        return ret

    json = {}
    for c in node.childNodes:
        if c.nodeType == c.TEXT_NODE:
            return c.data
        children = toJSON(c)
        attributes = processAttr(c.attributes)
        if attributes:
            if children.__class__ == str:
                children = {"value": children}
            children["attr"] = attributes
        if c.nodeName not in json:
            json[c.nodeName] = children
        else:
            if json[c.nodeName].__class__ != list:
                json[c.nodeName] = [json[c.nodeName]]
            json[c.nodeName].append(children)
    return json
